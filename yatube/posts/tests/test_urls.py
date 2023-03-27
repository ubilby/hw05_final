from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    def test_homepage(self):
        """закружается главная страница"""
        # Отправляем запрос через client,
        # созданный в setUp()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class DynamicURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # создаем группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.author = User.objects.create_user(  # type: ignore
            username='StasBasov'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=('Тестовый пост, проверяющий что метод __str__'
                  'отображает 15 знаков'
                  ),
            group=cls.group
        )
        cls.not_author = User.objects.create_user(  # type: ignore
            username='anyname'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def setUp(self):
        self.client.force_login(self.author)
        cache.clear()

    def test_pages_without_access_rights(self):
        '''страницы без прав доступа'''
        self.client.logout()
        guest_client_pages = {
            '/group/test/': HTTPStatus.OK,
            '/profile/StasBasov/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,  # type: ignore
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,  # type: ignore
            '/create/': HTTPStatus.FOUND,
            '/unknown/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.FOUND
        }

        for page, code in guest_client_pages.items():
            with self.subTest(page=page, code=code):
                response = self.client.get(page)
                self.assertEqual(response.status_code, code)

    def test_post_page_for_author(self):
        """закружается страница редактирования поста"""
        response = self.client.get(
            f'/posts/{self.post.id}/edit/'  # type: ignore
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_page_for_not_author(self):
        self.client.force_login(self.not_author)
        """не закружается страница редактирования поста не для автора"""
        response = self.client.get(
            f'/posts/{self.post.id}/edit/'  # type: ignore
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.client.logout()

    def test_post_create_page_(self):
        """закружается страница создания поста"""
        response = self.client.get('/create/')  # type: ignore
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """корректные шаблоны"""
        id = self.post.id  # type: ignore
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test/': 'posts/group_list.html',
            '/profile/StasBasov/': 'posts/profile.html',
            f'/posts/{id}/': 'posts/post_detail.html',
            f'/posts/{id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
