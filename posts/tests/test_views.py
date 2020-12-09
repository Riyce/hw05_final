import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage, Site
from django.core.files.uploadedfile import SimpleUploadedFile
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
        cls.Post_edit = reverse(
            'post_edit',
            kwargs={
                'username': PagesTests.post.author,
                'post_id': PagesTests.post.pk
            }
        )
        cls.Post_page = reverse(
            'post',
            kwargs={
                'username': PagesTests.post.author.username,
                'post_id': PagesTests.post.pk
            }
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
        response = PagesTests.author.get(PagesTests.Post_edit)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def author_correct_context(self):
        responses = [
            reverse('profile', kwargs={'username': PagesTests.user.username}),
            PagesTests.Post_page
        ]
        for url in responses:
            with self.subTest():
                response = PagesTests.author.get(url)
                author = response.context['author']
                self.assertEqual(author, PagesTests.user)

    def paginator_correct_context(self):
        responses = [
            reverse('index'),
            reverse('group', kwargs={'slug': 'test-slug'}),
            reverse('profile', kwargs={'username': PagesTests.user.username}),
            reverse('follow_index'),
        ]
        for url in responses:
            with self.subTest():
                response = PagesTests.author.get(url)
                paginator = response.context['paginator']
                self.assertEqual(paginator, 10)

    def post_correct_context(self):
        responses = [
            reverse('index'),
            reverse('group', kwargs={'slug': 'test-slug'}),
            reverse('profile', kwargs={'username': PagesTests.user.username}),
            PagesTests.Post_page,
        ]
        for url in responses:
            with self.subTest():
                request = PagesTests.author.get(url)
                post = request.context['page'][0]
                self.assertEqual(post, PagesTests.post)

    def test_flatpages_page_shows_correct_context(self):
        response1 = PagesTests.author.get('/about-author/')
        response2 = PagesTests.author.get('/about-spec/')
        author_title = response1.context.get('flatpage').title
        spec_title = response2.context.get('flatpage').title
        author_content = response1.context.get('flatpage').content
        spec_content = response2.context.get('flatpage').content
        self.assertEqual(author_title, PagesTests.flat_about.title)
        self.assertEqual(spec_title, PagesTests.flat_tech.title)
        self.assertEqual(author_content, PagesTests.flat_about.content)
        self.assertEqual(spec_content, PagesTests.flat_tech.content)

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
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': PagesTests.group1.pk,
            'text': 'Еще один тестовый текст',
            'image': uploaded,
        }
        PagesTests.author.post(
            PagesTests.Post_edit,
            data=form_data,
            follow=True,
        )
        post_response = PagesTests.author.get(PagesTests.Post_page)
        group_response = PagesTests.author.get(
                reverse('group', kwargs={'slug': PagesTests.group1.slug})
        )
        profile_response = PagesTests.author.get(
            reverse('profile', kwargs={'username': PagesTests.user.username})
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
        image = SimpleUploadedFile(
            name='small.txt',
            content=None,
            content_type='text/plain',
        )
        form_data = {
            'group': PagesTests.group1.pk,
            'text': 'Еще один тестовый текст',
            'image': image,
        }
        response = PagesTests.author.post(
            reverse('new_post',),
            data=form_data,
            follow=True,
        )
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_follow_page_for_user_with_following(self):
        response = PagesTests.authorized_client1.get(reverse('follow_index'))
        post = response.context['page'][0]
        self.assertEqual(post, PagesTests.post)

    def test_follow_page_for_user_without_following(self):
        response = PagesTests.authorized_client2.get(reverse('follow_index'))
        posts_count = response.context['paginator'].count
        self.assertEqual(posts_count, 0)

    def test_cache(self):
        page = PagesTests.guest_client.get(reverse('index')).content
        PagesTests.post.text = 'Новый текст поста'
        PagesTests.post.save()
        content1 = PagesTests.guest_client.get(reverse('index')).content
        self.assertEqual(content1, page)
        cache.clear()
        content2 = PagesTests.guest_client.get(reverse('index')).content
        self.assertNotEqual(content2, page)
