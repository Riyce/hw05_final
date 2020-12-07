import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage, Site
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post


class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug'
        )
        cls.site = Site.objects.get_current()
        cls.site.save()
        cls.flat_about = FlatPage.objects.create(
            url='/about-author/',
            title='Об авторе',
            content='<b>Здесь текст про автора</b>'
        )
        cls.flat_about.save()
        cls.flat_tech = FlatPage.objects.create(
            url='/about-spec/',
            title='О технологиях',
            content='<b>Здесь текст про технологии</b>'
        )
        cls.flat_tech.save()
        cls.flat_about.sites.add(cls.site)
        cls.flat_tech.sites.add(cls.site)
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            description='Тестовое описание группы 2',
            slug='test-slug2'
        )
        cls.guest_client = Client()
        cls.user = get_user_model().objects.create_user(username='Oleg')
        cls.user1 = get_user_model().objects.create_user(username='Olegson')
        cls.user2 = get_user_model().objects.create_user(username='Olegsana')
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user1,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=PagesTests.group1,
            author=cls.user,
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html':
            reverse('group', kwargs={'slug': PagesTests.group1.slug}),
            'profile.html':
            reverse('profile', kwargs={'username': PagesTests.user.username}),
            'post.html':
            reverse(
                'post',
                kwargs={
                    'username': PagesTests.post.author.username,
                    'post_id': PagesTests.post.pk
                }
            )
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest():
                response = PagesTests.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        response = PagesTests.author.get(reverse('index'))
        post_text = response.context.get('page')[0].text
        post_author = response.context.get('page')[0].author
        post_group = response.context.get('page')[0].group
        post_pub_date = response.context.get('page')[0].pub_date
        paginator = response.context.get('paginator').per_page
        posts_count = response.context.get('paginator').count
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_group, PagesTests.post.group)
        self.assertEqual(post_pub_date, PagesTests.post.pub_date)
        self.assertEqual(paginator, 10)
        self.assertEqual(posts_count, 1)

    def test_group_page_shows_correct_context(self):
        response = PagesTests.author.get(
            reverse('group', kwargs={'slug': 'test-slug'})
        )
        post_text = response.context.get('page')[0].text
        post_author = response.context.get('page')[0].author
        post_group = response.context.get('page')[0].group
        post_pub_date = response.context.get('page')[0].pub_date
        paginator = response.context.get('paginator').per_page
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_group, PagesTests.post.group)
        self.assertEqual(post_pub_date, PagesTests.post.pub_date)
        self.assertEqual(paginator, 10)

    def test_new_post_shows_correct_context(self):
        response = PagesTests.author.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_shows_correct_context(self):
        response = PagesTests.author.get(
            reverse(
                'post_edit',
                kwargs={
                    'username': PagesTests.post.author,
                    'post_id': PagesTests.post.pk
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        response = PagesTests.author.get(
            reverse('profile', kwargs={'username': PagesTests.user.username})
        )
        post_text = response.context.get('page')[0].text
        post_author = response.context.get('page')[0].author
        post_group = response.context.get('page')[0].group
        post_pub_date = response.context.get('page')[0].pub_date
        author_username = response.context.get('author').username
        author_posts_count = response.context.get('author').posts.count()
        paginator = response.context.get('paginator').per_page
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_group, PagesTests.post.group)
        self.assertEqual(post_pub_date, PagesTests.post.pub_date)
        self.assertEqual(author_username, PagesTests.user.username)
        self.assertEqual(author_posts_count, PagesTests.user.posts.count())
        self.assertEqual(paginator, 10)

    def test_post_page_shows_correct_context(self):
        response = PagesTests.author.get(
            reverse(
                'post',
                kwargs={
                    'username': PagesTests.post.author.username,
                    'post_id': PagesTests.post.pk
                }
            )
        )
        post_text = response.context.get('post').text
        post_author = response.context.get('post').author
        post_group = response.context.get('post').group
        post_pub_date = response.context.get('post').pub_date
        author_username = response.context.get('author').username
        author_posts_count = response.context.get('author').posts.count()
        self.assertEqual(post_text, PagesTests.post.text)
        self.assertEqual(post_author, PagesTests.post.author)
        self.assertEqual(post_group, PagesTests.post.group)
        self.assertEqual(post_pub_date, PagesTests.post.pub_date)
        self.assertEqual(author_username, PagesTests.user.username)
        self.assertEqual(author_posts_count, PagesTests.user.posts.count())

    def test_flatpages_page_shows_correct_context(self):
        response1 = PagesTests.author.get('/about-author/')
        response2 = PagesTests.author.get('/about-spec/')
        author_title = response1.context.get('flatpage').title
        spec_title = response2.context.get('flatpage').title
        author_content = response1.context.get('flatpage').content
        spec_content = response2.context.get('flatpage').content
        self.assertEqual(author_title, 'Об авторе')
        self.assertEqual(spec_title, 'О технологиях')
        self.assertEqual(author_content, '<b>Здесь текст про автора</b>')
        self.assertEqual(spec_content, '<b>Здесь текст про технологии</b>')

    def test_post_goes_to_correct_group(self):
        response1 = PagesTests.author.get(
            reverse('group', kwargs={'slug': PagesTests.group1.slug})
        )
        response2 = PagesTests.author.get(
            reverse('group', kwargs={'slug': PagesTests.group2.slug})
        )
        paginator1 = response1.context.get('paginator').count
        paginator2 = response2.context.get('paginator').count
        self.assertEqual(paginator1, 1)
        self.assertEqual(paginator2, 0)
        self.assertEqual(PagesTests.group1.posts.count(), 1)
        self.assertEqual(PagesTests.group2.posts.count(), 0)

    def test_images_on_page(self):
        with open('posts/tests/file.png', 'rb') as img:
            PagesTests.author.post(
                reverse(
                    'post_edit',
                    kwargs={
                        'username': PagesTests.user.username,
                        'post_id': PagesTests.post.pk
                    }
                ),
                {
                    'group': PagesTests.group1.pk,
                    'text': 'Еще один тестовый текст',
                    'image': img,
                },
                follow=True,
            )
            post_response = PagesTests.author.get(
                reverse(
                    'post',
                    kwargs={
                        'username': PagesTests.user.username,
                        'post_id': PagesTests.post.pk,
                    }
                )
            )
            group_response = PagesTests.author.get(
                reverse('group', kwargs={'slug': PagesTests.group1.slug})
            )
            profile_response = PagesTests.author.get(
                reverse(
                    'profile',
                    kwargs={'username': PagesTests.user.username}
                )
            )
            index_response = self.client.get(reverse('index'))
            images_on_pages = [
                post_response.context.get('post').image,
                index_response.context.get('page')[0].image,
                profile_response.context.get('page')[0].image,
                group_response.context.get('page')[0].image,
            ]
            for image in images_on_pages:
                with self.subTest():
                    self.assertTrue(image)

    def test_noimage_file(self):
        with open('posts/tests/text.txt', 'rb') as img:
            response = PagesTests.author.post(
                reverse('new_post',),
                {
                    'text': 'Еще один тестовый текст',
                    'image': img,
                },
                follow=True,
            )
            form = response.context.get('form')
            self.assertFalse(form.is_valid())

    def test_cache(self):
        response = PagesTests.guest_client.get(reverse('index'))
        self.assertContains(response, 'Тестовый текст')
        form_data = {
            'text': 'Кое-что поменяем.',
        }
        PagesTests.author.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': PagesTests.user.username,
                    'post_id': PagesTests.post.pk
                }
            ),
            data=form_data,
            follow=True,
        )
        response2 = PagesTests.guest_client.get(reverse('index'))
        self.assertContains(response2, 'Тестовый текст')
        cache.clear()
        response3 = PagesTests.guest_client.get(reverse('index'))
        self.assertContains(response3, form_data['text'])

    def test_follow_page(self):
        response1 = PagesTests.authorized_client1.get(reverse('follow_index'))
        response2 = PagesTests.authorized_client2.get(reverse('follow_index'))
        with_follow_count = response1.context.get('paginator').count
        without_follow_count = response2.context.get('paginator').count
        with_follow_text = response1.context.get('page')[0].text
        self.assertEqual(with_follow_count, 1)
        self.assertEqual(without_follow_count, 0)
        self.assertEqual(with_follow_text, 'Тестовый текст')
