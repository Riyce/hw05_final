import shutil
import tempfile

from django.conf import settings
from django.contrib.flatpages.models import FlatPage, Site
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User

SLUG1 = 'slug'
SLUG2 = 'slug2'
USERNAME1 = 'Oleg'
USERNAME2 = 'Olegson'
FOLLOW_INDEX = reverse('follow_index')
INDEX = reverse('index')
GROUP1 = reverse('group', args=[SLUG1])
GROUP2 = reverse('group', args=[SLUG2])
OLEG_PROFILE = reverse('profile', args=[USERNAME1])
ABOUT = reverse('about')
ABOUT_SPEC = reverse('about-spec')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug=SLUG1
        )
        cls.site = Site.objects.get_current()
        cls.flat_about = FlatPage.objects.create(
            url=ABOUT,
            title='Об авторе',
            content='<b>Здесь текст про автора</b>'
        )
        cls.flat_about.save()
        cls.flat_tech = FlatPage.objects.create(
            url=ABOUT_SPEC,
            title='О технологиях',
            content='<b>Здесь текст про технологии</b>'
        )
        cls.flat_tech.save()
        cls.flat_about.sites.add(cls.site)
        cls.flat_tech.sites.add(cls.site)
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            description='Тестовое описание группы 2',
            slug=SLUG2
        )
        cls.guest_client = Client()
        cls.oleg_user = User.objects.create_user(username=USERNAME1)
        cls.olegson_user = User.objects.create_user(username=USERNAME2)
        cls.oleg_post_creator_client = Client()
        cls.oleg_post_creator_client.force_login(cls.oleg_user)
        cls.olegson_read_only_client = Client()
        cls.olegson_read_only_client.force_login(cls.olegson_user)
        cls.follow = Follow.objects.create(
            author=cls.oleg_user,
            user=cls.olegson_user,
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            group=self.group1,
            author=self.oleg_user,
        )
        self.POST = reverse(
            'post',
            args=[self.post.author.username, self.post.pk]
        )
        self.EDIT = reverse(
            'post_edit',
            args=[self.post.author.username, self.post.pk]
        )

    def test_author_correct_context(self):
        urls = [
            OLEG_PROFILE,
            self.POST
        ]
        for url in urls:
            with self.subTest():
                response = self.olegson_read_only_client.get(url)
                author = response.context['author']
                self.assertEqual(author, self.oleg_user)

    def test_paginator_correct_context(self):
        responses = [
            INDEX,
            GROUP1,
            OLEG_PROFILE,
            FOLLOW_INDEX
        ]
        for url in responses:
            with self.subTest():
                response = self.olegson_read_only_client.get(url)
                paginator = response.context['paginator'].per_page
                self.assertEqual(paginator, 10)

    def test_post_correct_context(self):
        responses = [
            INDEX,
            GROUP1,
            OLEG_PROFILE,
            FOLLOW_INDEX,
            self.POST
        ]
        for url in responses:
            with self.subTest():
                request = self.olegson_read_only_client.get(url)
                if url == self.POST:
                    post = request.context['post']
                else:
                    post = request.context['page'][0]
                self.assertEqual(post, self.post)

    def test_flatpages_page_shows_correct_context(self):
        response1 = self.olegson_read_only_client.get(ABOUT)
        response2 = self.olegson_read_only_client.get(ABOUT_SPEC)
        author_title = response1.context['flatpage'].title
        spec_title = response2.context['flatpage'].title
        author_content = response1.context['flatpage'].content
        spec_content = response2.context['flatpage'].content
        self.assertEqual(author_title, self.flat_about.title)
        self.assertEqual(spec_title, self.flat_tech.title)
        self.assertEqual(author_content, self.flat_about.content)
        self.assertEqual(spec_content, self.flat_tech.content)

    def test_group_without_post(self):
        response = self.olegson_read_only_client.get(GROUP2)
        paginator = response.context.get('paginator').count
        self.assertEqual(paginator, 0)
        self.assertEqual(self.group2.posts.count(), 0)

    def test_add_image_to_post(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Еще один тестовый текст',
            'group': self.group1.pk,
            'image': uploaded,
        }
        self.oleg_post_creator_client.post(
            self.EDIT,
            data=form_data,
            follow=True,
        )
        post = Post.objects.all().first()
        self.assertEqual(post.image.size, form_data['image'].size)
        responses = [
            INDEX,
            GROUP1,
            OLEG_PROFILE,
            FOLLOW_INDEX,
            self.POST
        ]
        for url in responses:
            with self.subTest():
                request = self.olegson_read_only_client.get(url)
                if url == self.POST:
                    image = request.context['post'].image
                else:
                    image = request.context['page'][0].image
                self.assertTrue(image)
                self.assertEqual(image.size, form_data['image'].size)

    def test_follow_page_for_user_without_following(self):
        response = self.oleg_post_creator_client.get(FOLLOW_INDEX)
        posts_count = response.context['paginator'].count
        self.assertEqual(posts_count, 0)

    def test_cache(self):
        test_page = self.guest_client.get(INDEX).content
        self.post.text = 'Новый текст поста'
        self.post.save()
        page1 = self.guest_client.get(INDEX).content
        self.assertEqual(page1, test_page)
        cache.clear()
        page2 = self.guest_client.get(INDEX).content
        self.assertNotEqual(page2, test_page)
