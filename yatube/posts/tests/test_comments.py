from django.shortcuts import get_object_or_404
from django.test import TestCase
from django.urls import reverse

from posts.models import Comment, Post, User


class CommentsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='user1')  # type: ignore
        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовый пост",
        )

    def setUp(self):
        self.client.force_login(self.author)

    def test_not_authorized_user_cant_comment(self):
        self.client.logout()
        before_count = Comment.objects.count()
        self.client.post(
            reverse(
                'post:add_comment',
                kwargs={"post_id": self.post.id}  # type: ignore
            ),
            {'text': 'test'}
        )
        after_count = Comment.objects.count()
        self.assertEqual(before_count, after_count)

    def test_authorized_user_can_comment(self):
        before_count = Comment.objects.count()
        self.client.post(
            reverse(
                'post:add_comment',
                kwargs={"post_id": self.post.id}  # type: ignore
            ),
            {'text': 'test'}
        )
        after_count = Comment.objects.count()
        self.assertEqual(before_count, after_count - 1)

    def test_adding_comments_to_post(self):
        text = 'another text'
        id = self.post.id  # type: ignore
        self.client.post(
            reverse(
                'post:add_comment',
                kwargs={"post_id": id}
            ),
            {'text': text}
        )
        last_comment = get_object_or_404(
            Post.objects.select_related(),
            id=id
        ).comments.all()[0].text  # type: ignore
        self.assertEqual(last_comment, text)
