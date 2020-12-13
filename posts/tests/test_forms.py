from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

USERNAME = 'Oleg'
SLUG = 'test-slug'
INDEX = reverse('index')
NEW = reverse('new_post')


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug=SLUG,
        )
        cls.form = PostForm()

    def setUp(self):
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        self.EDIT = reverse(
            'post_edit', args=[USERNAME, self.post.pk]
        )

    def test_new_post_shows_correct_context(self):
        response = self.authorized_client.get(NEW)
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
        response = self.authorized_client.get(self.EDIT)
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
        response = self.authorized_client.post(
            NEW,
            data=form_data,
            follow=True
        )
        count2 = Post.objects.all().count()
        self.assertEqual(count2, 1)
        post = response.context['page'][0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])

    def test_edit_post(self):
        form_data = {
            'text': 'Тестовый текст измененный',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            self.EDIT,
            data=form_data,
            follow=True,
        )
        count = Post.objects.all().count()
        self.assertEqual(count, 1)
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
