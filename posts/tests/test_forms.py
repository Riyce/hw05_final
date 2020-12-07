from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user(username='Oleg')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.form = PostForm()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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
        }
        response = PostFormTests.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            Post.objects.filter(author=PostFormTests.user).first().text,
            'Тестовый текст другого поста'
        )

    def test_edit_post(self):
        form_data = {
            'text': 'Тестовый текст измененный',
        }
        PostFormTests.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': PostFormTests.user,
                    'post_id': PostFormTests.post.pk,
                }
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Post.objects.filter(author=PostFormTests.user).first().text,
            'Тестовый текст измененный'
        )
