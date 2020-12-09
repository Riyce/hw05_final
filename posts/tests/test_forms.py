from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Oleg')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.form = PostForm()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.Postedit = reverse(
                'post_edit',
                kwargs={
                    'username': cls.user,
                    'post_id': cls.post.pk,
                }
            )

    def test_help_texts(self):
        help_texts = {
            'group': 'Выберете группу из списка доступных.',
            'text': 'Введите текст Вашего поста.',
        }
        for field, value in help_texts.items():
            with self.subTest():
                help_text = PostFormTests.form.fields[field].help_text
                self.assertEqual(help_text, value)

    def test_labels(self):
        labels = {
            'group': 'Выберете группу',
            'text': 'Текст',
        }
        for field, value in labels.items():
            with self.subTest():
                label = PostFormTests.form.fields[field].label
                self.assertEqual(label, value)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст другого поста',
            'group': PostFormTests.group.pk,
        }
        response = PostFormTests.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        text = response.context['post'].text
        group = response.context['post'].group
        author = response.context['post'].author
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group.pk, form_data['group'])
        self.assertEqual(author, PostFormTests.user)

    def test_edit_post(self):
        form_data = {
            'text': 'Тестовый текст измененный',
            'group': PostFormTests.group.pk,
        }
        response = PostFormTests.authorized_client.post(
            PostFormTests.Postedit,
            data=form_data,
            follow=True,
        )
        text = response.context['post'].text
        group = response.context['post'].group
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group.pk, form_data['group'])
