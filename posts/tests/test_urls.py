from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user1 = User.objects.create_user(username='Oleg')
        cls.user2 = User.objects.create_user(username='Olegson')
        cls.author = Client()
        cls.author.force_login(cls.user1)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user2)
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )
        cls.site = Site.objects.get_current()
        cls.site.save()
        cls.flat_about = FlatPage.objects.create(
            url='/about-author/',
            title='about me',
            content='<b>content</b>'
        )
        cls.flat_about.save()
        cls.flat_tech = FlatPage.objects.create(
            url='/about-spec/',
            title='about my tech',
            content='<b>content</b>'
        )
        cls.flat_tech.save()
        cls.flat_about.sites.add(cls.site)
        cls.flat_tech.sites.add(cls.site)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user1,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug'
        )
        cls.Post_page = reverse(
            'post',
            kwargs={
                'username': StaticURLTests.user1.username,
                'post_id': StaticURLTests.post.pk
            }
        )
        cls.Post_edit_page = reverse(
            'post_edit',
            kwargs={
                'username': StaticURLTests.user1.username,
                'post_id': StaticURLTests.post.pk
            }
        )
        cls.Add_comment = reverse(
            'add_comment',
            kwargs={
                'username': StaticURLTests.user1.username,
                'post_id': StaticURLTests.post.pk
            }
        )

    def test_pages_for_client(self):
        status_codes = {
            reverse('index'): 200,
            reverse('new_post'): 302,
            reverse(
                'group',
                kwargs={'slug': StaticURLTests.group.slug, }
            ):
            200,
            reverse(
                'profile',
                kwargs={'username': StaticURLTests.user1.username, }
            ):
            200,
            StaticURLTests.Post_page: 200,
            StaticURLTests.Post_edit_page: 302,
            reverse('about'): 200,
            reverse('about-spec'): 200,
            StaticURLTests.Add_comment: 302,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = StaticURLTests.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_pages_for_user(self):
        status_codes = {
            reverse('index'): 200,
            reverse('new_post'): 200,
            reverse(
                'group',
                kwargs={'slug': StaticURLTests.group.slug, }
            ):
            200,
            reverse(
                'profile',
                kwargs={'username': StaticURLTests.user1.username, }
            ):
            200,
            StaticURLTests.Post_page: 200,
            StaticURLTests.Post_edit_page: 302,
            reverse('about'): 200,
            reverse('about-spec'): 200,
            '/example/': 404,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = StaticURLTests.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_reditect_from_edit_page(self):
        redirects = {
            StaticURLTests.guest_client: StaticURLTests.Post_page,
            StaticURLTests.authorized_client: StaticURLTests.Post_page,
        }
        for users, adress in redirects.items():
            with self.subTest():
                response = users.post(StaticURLTests.Post_edit_page)
                self.assertRedirects(response, adress)

    def test_edit_post_page_for_author(self):
        response = StaticURLTests.author.get(StaticURLTests.Post_edit_page)
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            reverse('index'): 'index.html',
            reverse('new_post'): 'new.html',
            reverse(
                'group',
                kwargs={'slug': StaticURLTests.group.slug, }
            ):
            'group.html',
            StaticURLTests.Post_edit_page: 'new.html',
            reverse('about'): 'flatpages/default.html',
            reverse('about-spec'): 'flatpages/default.html',
            reverse(
                'profile',
                kwargs={'username': StaticURLTests.user1.username, }
            ):
            'profile.html',
            reverse('follow_index'): 'follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = StaticURLTests.author.get(url)
                self.assertTemplateUsed(response, template)

    def test_folloing(self):
        count = StaticURLTests.user2.follower.count()
        StaticURLTests.authorized_client.get(
            reverse(
                'profile_follow',
                kwargs={'username': StaticURLTests.user1.username}
            )
        )
        follow = Follow.objects.last()
        user = follow.user
        author = follow.author
        self.assertEqual(StaticURLTests.user2.follower.count(), count+1)
        self.assertEqual(user, StaticURLTests.user2)
        self.assertEqual(author, StaticURLTests.user1)

    def test_unfolloing(self):
        count = StaticURLTests.user1.follower.count()
        StaticURLTests.author.get(
            reverse(
                'profile_unfollow',
                kwargs={'username': StaticURLTests.user2.username}
            )
        )
        self.assertEqual(StaticURLTests.user2.follower.count(), count-1)
