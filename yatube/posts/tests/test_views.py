from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем группы
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test1',
            description='Тестовое описание',
        )
        # Создаем авторизованый клиент для написания поста
        cls.author = User.objects.create_user(username='user1')  # type: ignore
        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовый пост",
            group=cls.group
        )
        cls.author_2 = User.objects.create_user(  # type: ignore
            username='user2'
        )
        cls.post_author_2_no_group = Post.objects.create(
            author=cls.author_2,
            text='Тестовый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def setUp(self):
        cache.clear()
        self.client.force_login(self.author)

    # Проверяем используемые шаблоны
    def test_views_correct_template(self):
        """View использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_page_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': (
                        self.post.id  # type: ignore
                    )
                }
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': (
                        self.post.id  # type: ignore
                    )
                }
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_list_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        reverse_names = {
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ): self.post,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): self.post,
            reverse('posts:index'): self.post_author_2_no_group,
        }

        for reverse_name, post in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author
                post_text_0 = first_object.text
                post_group_0 = first_object.group
                self.assertEqual(post_author_0, post.author)
                self.assertEqual(post_text_0, post.text)
                self.assertEqual(post_group_0, post.group)

    def test_post_detail(self):
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': (
                        self.post_author_2_no_group.id  # type: ignore
                    )
                }
            )
        )
        post_object_id = response.context['post'].id
        posts_count = response.context['count']
        self.assertEqual(
            post_object_id,
            self.post_author_2_no_group.id,  # type: ignore
            'Передан другой пост'
        )
        self.assertEqual(
            posts_count,
            Post.objects.all().filter(
                author_id=self.author_2.id
            ).count(),
            'Количество постов не соответствует ожидаемому'
        )

    def test_404_give_right_template(self):
        template = 'core/404.html'
        response = self.client.get('/unknown_adress/')
        self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test1',
            description='Тестовое описание',
        )
        cls.author = User.objects.create_user(username='user1')  # type: ignore
        cls.posts_of_user_1_group_1 = Post.objects.bulk_create([
            Post(
                author=cls.author,
                text=f'Тестовый пост {i+1}',
                group=cls.group_1
            ) for i in range(13)
        ])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('post:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('post:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_page_contains_ten_records(self):
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.group_1.slug}
            )
        )
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_1.slug}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_ten_records(self):
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
