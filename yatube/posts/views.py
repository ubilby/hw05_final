from django.core.paginator import Paginator, Page
from django.db.models.query import QuerySet
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpRequest
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post, User


def get_page_obj(posts: QuerySet, request: HttpRequest) -> Page:
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


def index(request) -> HttpResponse:
    template = 'posts/index.html'
    page_obj = get_page_obj(Post.objects.all(), request)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_list(request, slug):
    group = get_object_or_404(
        Group.objects.select_related(), slug=slug
    )
    page_obj = get_page_obj(group.posts.all(), request)  # type: ignore
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(
        User.objects.select_related(), username=username
    )
    page_obj = get_page_obj(author.posts.all(), request)  # type: ignore
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user)  # type: ignore
    )
    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        id=post_id
    )
    form = CommentForm(request.POST)
    count = Post.objects.filter(
        author_id=post.author.id  # type: ignore
    ).count()
    comments = Comment.objects.filter(
        post=post_id
    ).select_related('author')
    context = {
        'form': form,
        'count': count,
        'text': post.text[0:30],
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
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = get_page_obj(
        Post.objects.filter(author__following__user=request.user),
        request
    )
    context = {'page_obj': page_obj}

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, id=request.user.id)
    author = get_object_or_404(User, username=username)

    if not (user == author):
        Follow.objects.get_or_create(
            user=user,
            author=author
        )

    return redirect('post:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow,
        author=get_object_or_404(User, username=username),
        user=request.user
    )
    follow.delete()

    return redirect('post:profile', username=username)
