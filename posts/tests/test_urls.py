from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User

USERNAME1 = 'Oleg'
USERNAME2 = 'Olegson'
SLUG = 'test-slug'
INDEX = reverse('index')
FOLLOW_PAGE = reverse('follow_index')
GROUP = reverse('group', args=[SLUG])
NEW = reverse('new_post')
PROFILE = reverse('profile', args=[USERNAME2])
ABOUT = reverse('about')
ABOUT_SPEC = reverse('about-spec')
NOT_FOUND = '/example/'
FOLLOW = reverse('profile_follow', args=[USERNAME1])
UNFOLLOW = reverse('profile_unfollow', args=[USERNAME2])
AUTHOR_URL = '/about-author/'
SPEC_URL = '/about-spec/'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user1 = User.objects.create_user(username=USERNAME1)
        cls.user2 = User.objects.create_user(username=USERNAME2)
        cls.author_client = Client()
        cls.author_client.force_login(cls.user1)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user2)
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )
        cls.site = Site.objects.get_current()
        cls.site.save()
        cls.flat_about = FlatPage.objects.create(
            url=AUTHOR_URL,
            title='about me',
            content='<b>content</b>'
        )
        cls.flat_about.save()
        cls.flat_tech = FlatPage.objects.create(
            url=SPEC_URL,
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
            slug=SLUG
        )
        cls.POST = reverse(
            'post',
            args=[USERNAME1, cls.post.pk]
        )
        cls.EDIT = reverse(
            'post_edit',
            args=[USERNAME1, cls.post.pk]
        )
        cls.ADD = reverse(
            'add_comment',
            args=[USERNAME1, cls.post.pk]
        )
        cls.REDIRECT = (
            reverse('login') +
            '?next=' +
            cls.EDIT
        )

    def test_pages_for_client(self):
        status_codes = {
            INDEX: 200,
            FOLLOW_PAGE: 302,
            NEW: 302,
            GROUP: 200,
            PROFILE: 200,
            ABOUT: 200,
            ABOUT_SPEC: 200,
            NOT_FOUND: 404,
            self.POST: 200,
            self.EDIT: 302,
            self.ADD: 302,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_pages_for_authorized_client(self):
        status_codes = {
            INDEX: 200,
            NEW: 200,
            FOLLOW_PAGE: 200,
            GROUP: 200,
            PROFILE: 200,
            ABOUT: 200,
            ABOUT_SPEC: 200,
            NOT_FOUND: 404,
            self.POST: 200,
            self.EDIT: 302,
        }
        for url, code in status_codes.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_redirect(self):
        redirects = {
            self.guest_client: self.REDIRECT,
            self.authorized_client: self.POST,
        }
        for client, url in redirects.items():
            with self.subTest():
                response = client.post(self.EDIT)
                self.assertRedirects(response, url)

    def test_edit_post_page_for_author(self):
        response = self.author_client.get(self.EDIT)
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            INDEX: 'index.html',
            NEW: 'new.html',
            GROUP: 'group.html',
            ABOUT: 'flatpages/default.html',
            ABOUT_SPEC: 'flatpages/default.html',
            PROFILE: 'profile.html',
            FOLLOW_PAGE: 'follow.html',
            self.POST: 'post.html',
            self.EDIT: 'new.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_following(self):
        self.authorized_client.get(FOLLOW)
        follow = Follow.objects.filter(
            user=self.user2, author=self.user1
        ).exists()
        self.assertTrue(follow)

    def test_unfollowing(self):
        self.author_client.get(UNFOLLOW)
        follow = Follow.objects.filter(
            user=self.user1, author=self.user2
        ).exists()
        self.assertFalse(follow)
