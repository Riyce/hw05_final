from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'Oleg'
        cls.user = User.objects.create_user(username=cls.username)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        cls.form = PostForm()
        cls.INDEX = reverse('index')
        cls.NEW = reverse('new_post')

    def setUp(self):
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        self.EDIT = reverse(
            'post_edit', args=[self.username, self.post.pk]
        )

    def test_new_post_shows_correct_context(self):
        response = self.author.get(self.NEW)
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
        response = self.author.get(self.EDIT)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_help_texts(self):
        help_texts = {
            'group': 'Выберете группу из списка доступных.',
            'text': 'Введите текст Вашего поста.',
        }
        for field, value in help_texts.items():
            with self.subTest():
                help_text = self.form.fields[field].help_text
                self.assertEqual(help_text, value)

    def test_labels(self):
        labels = {
            'group': 'Выберете группу',
            'text': 'Текст',
        }
        for field, value in labels.items():
            with self.subTest():
                label = self.form.fields[field].label
                self.assertEqual(label, value)

    def test_create_post(self):
        Post.objects.all().delete()
        count1 = Post.objects.all().count()
        self.assertEqual(count1, 0)
        form_data = {
            'text': 'Тестовый текст другого поста',
            'group': self.group.pk,
        }
        self.author.post(
            self.NEW,
            data=form_data,
            follow=True
        )
        count2 = Post.objects.all().count()
        post = Post.objects.all().first()
        text = post.text
        group = post.group
        self.assertEqual(count2, 1)
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group.pk, form_data['group'])

    def test_edit_post(self):
        count = Post.objects.all().count()
        self.assertEqual(count, 1)
        form_data = {
            'text': 'Тестовый текст измененный',
            'group': self.group.pk,
        }
        self.author.post(
            self.EDIT,
            data=form_data,
            follow=True,
        )
        post = Post.objects.all().first()
        text = post.text
        group = post.group
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group.pk, form_data['group'])
