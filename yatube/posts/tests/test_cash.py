from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from posts.models import Post, User


class CashTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='user1')  # type: ignore
        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовый пост",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def setUp(self):
        self.client.force_login(self.author)
        cache.clear()

    def test_cache_index_page_by_adding_post(self):
        response = self.client.get(reverse('posts:index'))
        posts_at_db_before = Post.objects.all().count()
        posts_at_index_before = len(response.context['page_obj'])
        Post.objects.create(
            author=self.author,
            text='test1',
        )
        posts_at_db_after = Post.objects.all().count()
        response = self.client.get(reverse('posts:index'))
        posts_at_index_after = str(response.content).count('/posts/')
        self.assertEqual(posts_at_db_before, posts_at_db_after - 1)
        self.assertEqual(posts_at_index_before, posts_at_index_after)
