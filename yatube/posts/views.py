from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import (
    # get_list_or_404,
    get_object_or_404,
    redirect,
    render
)
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request) -> HttpResponse:
    template = 'posts/index.html'
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_list(request, slug):
    group = get_object_or_404(
        Group.objects.select_related(), slug=slug
    )
    posts = group.posts.all()  # type: ignore
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(
        User.objects.select_related(), username=username
    )
    paginator = Paginator(author.posts.all(), 10)  # type: ignore
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated and (
        author.following.filter(user=request.user)  # type: ignore
    ):
        following = True
    else:
        following = False

    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # на будущее хочу использовать здесь эту конструкцию
    # или похожую, чтобы остался один запрос к базе
    # comments = get_list_or_404(
    #     Comment.objects.select_related(),
    #     post_id=post_id
    # )
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        id=post_id
    )
    form = CommentForm(request.POST)
    text = post.text[0:30]
    count = Post.objects.filter(
        author_id=post.author.id  # type: ignore
    ).count()
    comments = Comment.objects.filter(
        post=post_id
    ).select_related('author')

    context = {
        'form': form,
        'count': count,
        'text': text,
        'post': post,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post:profile', request.user)

    else:
        form = PostForm()

    context = {
        'form': form,
        'is_edit': False
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    current_post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=current_post
    )

    if current_post.author != request.user:
        return redirect('post:post_detail', post_id=post_id)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post:post_detail', post_id=post_id)

    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    user = get_object_or_404(User, id=request.user.id)
    author = get_object_or_404(User, username=username)

    if (
        not (user == author)
        and not Follow.objects.filter(user=user, author=author).count()
    ):
        Follow.objects.create(
            user=user,
            author=author
        )
    return redirect('post:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    follow = get_object_or_404(
        Follow,
        author=get_object_or_404(User, username=username),
        user=request.user
    )
    follow.delete()
    return redirect('post:profile', username=username)
