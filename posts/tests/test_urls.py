from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.username1 = 'Oleg'
        cls.username2 = 'Olegson'
        cls.user1 = User.objects.create_user(username=cls.username1)
        cls.user2 = User.objects.create_user(username=cls.username2)
        cls.author = Client()
        cls.author.force_login(cls.user1)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user2)
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )
        cls.follow.save()
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
        cls.slug = 'test-slug'
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug=cls.slug
        )
        cls.INDEX = reverse('index')
        cls.FOLLOW_PAGE = reverse('follow_index')
        cls.GROUP = reverse('group', args=[cls.slug])
        cls.NEW = reverse('new_post')
        cls.PROFILE = reverse('profile', args=[cls.username1])
        cls.ABOUT = reverse('about')
        cls.ABOUT_SPEC = reverse('about-spec')
        cls.NOT_FOUND = '/example/'

    def test_pages_for_client(self):
        status_codes = {
            self.INDEX: 200,
            self.FOLLOW_PAGE: 302,
            self.NEW: 302,
            self.GROUP: 200,
            self.PROFILE: 200,
            self.ABOUT: 200,
            self.ABOUT_SPEC: 200,
            self.NOT_FOUND: 404,
            reverse('post', args=[self.username1, self.post.pk]): 200,
            reverse('post_edit', args=[self.username1, self.post.pk]): 302,
            reverse('add_comment', args=[self.username1, self.post.pk]): 302,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_pages_for_user(self):
        status_codes = {
            self.INDEX: 200,
            self.NEW: 200,
            self.FOLLOW_PAGE: 200,
            self.GROUP: 200,
            self.PROFILE: 200,
            self.ABOUT: 200,
            self.ABOUT_SPEC: 200,
            self.NOT_FOUND: 404,
            reverse('post', args=[self.username1, self.post.pk]): 200,
            reverse('post_edit', args=[self.username1, self.post.pk]): 302,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_redirect(self):
        redirects = {
            self.guest_client:
            reverse('login')
            + '?next='
            + reverse('post_edit', args=[self.username1, self.post.pk]),
            self.authorized_client:
            reverse('post', args=[self.user1.username, self.post.pk]),
        }
        for client, url in redirects.items():
            with self.subTest():
                response = client.post(
                    reverse('post_edit', args=[self.username1, self.post.pk])
                )
                self.assertRedirects(response, url)

    def test_edit_post_page_for_author(self):
        response = self.author.get(
            reverse('post_edit', args=[self.username1, self.post.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.INDEX: 'index.html',
            self.NEW: 'new.html',
            self.GROUP: 'group.html',
            self.ABOUT: 'flatpages/default.html',
            self.ABOUT_SPEC: 'flatpages/default.html',
            self.PROFILE: 'profile.html',
            self.FOLLOW_PAGE: 'follow.html',
            reverse('post', args=[self.username1, self.post.pk]): 'post.html',
            reverse('post_edit', args=[self.username1, self.post.pk]):
            'new.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.author.get(url)
                self.assertTemplateUsed(response, template)

    def test_following(self):
        self.authorized_client.get(
            reverse(
                'profile_follow',
                args=[self.username1]
            )
        )
        follow = Follow.objects.filter(
            user=self.user2, author=self.user1
        ).exists()
        self.assertTrue(follow)

    def test_unfollowing(self):
        self.author.get(
            reverse('profile_unfollow', args=[self.username2])
        )
        follow = Follow.objects.filter(
            user=self.user1, author=self.user2
        ).exists()
        self.assertFalse(follow)
