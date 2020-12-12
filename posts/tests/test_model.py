from django.test import TestCase

from posts.models import Group, Post, User

USERNAME = 'Oleg'
SLUG = 'slug'


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.post = Post.objects.create(
            text='Тестовый текст с длиной больше 15 символов',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое поисание',
            slug=SLUG
        )

    def test_group_verbose_name(self):
        group = self.group
        verbose = group._meta.get_field('title').verbose_name
        self.assertEquals(verbose, 'Название группы')

    def test_group_name_is_title_fild(self):
        group = self.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))

    def test_post_verbose_name(self):
        post = self.post
        verbose = post._meta.get_field('text').verbose_name
        self.assertEquals(verbose, 'Текст')

    def test_post_text_is_title_fild(self):
        post = self.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post))
