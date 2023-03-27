from django.test import TestCase
from django.urls import reverse

from posts.models import Follow, Post, User


class CashTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(  # type: ignore
            username='author'
        )
        cls.user = User.objects.create_user(username='user')  # type: ignore
        cls.another_user = User.objects.create_user(  # type: ignore
            username='another_user'
        )
        Follow.objects.create(
            user=cls.another_user,
            author=cls.author
        )
        Post.objects.create(
            author=cls.author,
            text='text'
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_authorisde_user_can_follow_and_unfollow(self):
        follower_count_before = self.user.follower.all().count()
        self.client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        follower_count_after = self.user.follower.all().count()
        self.assertEqual(follower_count_before, follower_count_after - 1)
        self.client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        follower_count_finally = self.user.follower.all().count()
        self.assertEqual(follower_count_before, follower_count_finally)

    def test_post_apears_on_feed(self):
        response = self.client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        self.client.logout()
        self.client.force_login(self.another_user)
        response = self.client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
