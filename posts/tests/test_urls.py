from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User

USERNAME1 = 'Oleg'
USERNAME2 = 'Olegson'
SLUG = 'test-slug'
INDEX = reverse('index')
FOLLOW_INDEX = reverse('follow_index')
GROUP = reverse('group', args=[SLUG])
NEW = reverse('new_post')
OLEGSON_PROFILE = reverse('profile', args=[USERNAME2])
ABOUT = reverse('about')
ABOUT_SPEC = reverse('about-spec')
LOGIN = reverse('login')
REDIRECT_AFTER_LOGIN_TO = f'{LOGIN}?next='
NEW_REDIRECT = REDIRECT_AFTER_LOGIN_TO + NEW
FOLLOW_INDEX_REDIRECT = REDIRECT_AFTER_LOGIN_TO + FOLLOW_INDEX
NOT_FOUND = '/example/'
OLEGSON_FOLLOW = reverse('profile_follow', args=[USERNAME1])
OLEG_UNFOLLOW = reverse('profile_unfollow', args=[USERNAME2])


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.oleg_user = User.objects.create_user(username=USERNAME1)
        cls.olegson_user = User.objects.create_user(username=USERNAME2)
        cls.guest_client = Client()
        cls.oleg_post_creator_client = Client()
        cls.oleg_post_creator_client.force_login(cls.oleg_user)
        cls.olegson_read_only_client = Client()
        cls.olegson_read_only_client.force_login(cls.olegson_user)
        cls.follow = Follow.objects.create(
            user=cls.oleg_user,
            author=cls.olegson_user,
        )
        cls.site = Site.objects.get_current()
        cls.site.save()
        cls.flat_about = FlatPage.objects.create(
            url=ABOUT,
            title='about me',
            content='<b>content</b>'
        )
        cls.flat_about.save()
        cls.flat_tech = FlatPage.objects.create(
            url=ABOUT_SPEC,
            title='about my tech',
            content='<b>content</b>'
        )
        cls.flat_tech.save()
        cls.flat_about.sites.add(cls.site)
        cls.flat_tech.sites.add(cls.site)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.oleg_user,
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
        cls.ADD_COMMENT = reverse(
            'add_comment',
            args=[USERNAME1, cls.post.pk]
        )
        cls.EDIT_PAGE_REDIRECT = REDIRECT_AFTER_LOGIN_TO + cls.EDIT
        cls.ADD_COMMENT_REDIRECT = REDIRECT_AFTER_LOGIN_TO + cls.ADD_COMMENT

    def test_pages_status_codes_for_clients(self):
        status_codes = {
            self.olegson_read_only_client:
            {
                INDEX: 200,
                NEW: 200,
                FOLLOW_INDEX: 200,
                GROUP: 200,
                OLEGSON_PROFILE: 200,
                ABOUT: 200,
                ABOUT_SPEC: 200,
                NOT_FOUND: 404,
                self.POST: 200,
                self.EDIT: 302
            },
            self.guest_client:
            {
                INDEX: 200,
                NEW: 302,
                FOLLOW_INDEX: 302,
                GROUP: 200,
                OLEGSON_PROFILE: 200,
                ABOUT: 200,
                ABOUT_SPEC: 200,
                NOT_FOUND: 404,
                self.POST: 200,
                self.EDIT: 302,
                self.ADD_COMMENT: 302
            },
            self.oleg_post_creator_client:
            {
                self.EDIT: 200,
            }
        }
        for client, data in status_codes.items():
            for url, ststus_code in data.items():
                with self.subTest():
                    response = client.get(url)
                    self.assertEqual(response.status_code, ststus_code)

    def test_redirects(self):
        redirects = {
            self.guest_client:
            {
                self.EDIT: self.EDIT_PAGE_REDIRECT,
                NEW: NEW_REDIRECT,
                FOLLOW_INDEX: FOLLOW_INDEX_REDIRECT,
                self.ADD_COMMENT: self.ADD_COMMENT_REDIRECT,
            },
            self.olegson_read_only_client:
            {
                self.EDIT: self.POST
            }
        }
        for client, redirect in redirects.items():
            for url, redirect_url in redirect.items():
                with self.subTest():
                    response = client.get(url)
                    self.assertRedirects(response, redirect_url)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            INDEX: 'index.html',
            NEW: 'new.html',
            GROUP: 'group.html',
            ABOUT: 'flatpages/default.html',
            ABOUT_SPEC: 'flatpages/default.html',
            OLEGSON_PROFILE: 'profile.html',
            FOLLOW_INDEX: 'follow.html',
            self.POST: 'post.html',
            self.EDIT: 'new.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.oleg_post_creator_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_following(self):
        self.olegson_read_only_client.get(OLEGSON_FOLLOW)
        follow = Follow.objects.filter(
            user=self.olegson_user, author=self.oleg_user
        ).exists()
        self.assertTrue(follow)

    def test_unfollowing(self):
        self.oleg_post_creator_client.get(OLEG_UNFOLLOW)
        follow = Follow.objects.filter(
            user=self.oleg_user, author=self.olegson_user
        ).exists()
        self.assertFalse(follow)
