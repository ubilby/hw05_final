import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test',
            description='Тестовое описание',
        )
        cls.author = User.objects.create_user(username='user3')  # type: ignore
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_page_show_correct_context(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('post:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form'
                ).fields.get(value)  # type: ignore
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
        self.client.logout()

    def test_edit_post_page_show_correct_context(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                'post:post_edit',
                kwargs={
                    'post_id': (
                        self.post.id  # type: ignore
                    )
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form'
                ).fields.get(value)  # type: ignore
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
        self.client.logout()

    def test_not_authorized_user_cant_post(self):
        before_count = Post.objects.all().count()
        self.client.post(
            reverse('post:post_create'),
            {'text': 'test'}
        )
        after_count = Post.objects.all().count()
        self.assertEqual(before_count, after_count)

    def test_authorized_user_can_post(self):
        self.client.force_login(self.author)
        before_count = Post.objects.count()
        response = self.client.post(
            reverse('post:post_create'),
            {
                'text': 'test1',
            }
        )
        after_count = Post.objects.count()
        self.assertEqual(before_count, after_count - 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text='test1',
            ).exists()
        )
        self.client.logout()

    def test_image_add_to_pages(self):
        self.client.force_login(self.author)
        before_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        response = self.client.post(
            reverse('post:post_create'),
            data={
                'text': 'test',
                'group': self.group.pk,
                'image': uploaded,
                'follow': True,
            }
        )
        after_count = Post.objects.count()

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )

        reverse_names = [
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse('posts:index'),
        ]

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                image_name = response.context['page_obj'][0].image.name
                self.assertEqual(image_name, 'posts/small.gif')

        post_id = response.context['page_obj'][0].pk
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            ),
        )
        image_name = response.context['post'].image.name
        self.assertEqual(image_name, 'posts/small.gif')
        self.assertEqual(before_count, after_count - 1)
        self.assertTrue(
            Post.objects.filter(
                text='test',
                image='posts/small.gif'
            ).exists()
        )
        self.client.logout()
