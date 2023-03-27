from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')  # type: ignore
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Тестовый пост, проверяющий что метод __str__'
                  'отображает 15 знаков'
                  ),
            group=cls.group
        )

    def test_post_str(self):
        """post.__str__ работает ожидаемо"""
        with self.subTest(value='text'):
            self.assertEqual(
                f'{self.post}', self.post.text[:15])

    def test_group_str(self):
        """group.__str__ работает ожидаемо"""
        with self.subTest(value='text'):
            self.assertEqual(
                f'{self.group}', self.group.title)

    def test_post_verbose_name(self):
        """verbose_name в полях post-a совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях post совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)
