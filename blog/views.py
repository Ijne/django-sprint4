"""Представления Blogicum."""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post


POSTS_PER_PAGE = 10
User = get_user_model()


class RegisterView(CreateView):
    """Регистрация нового пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


def post_queryset():
    """Вернуть публикации с объектами связей и числом комментариев."""
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


def public_posts():
    """Вернуть доступные всем публикации."""
    return post_queryset().filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    )


def paginate(request, queryset):
    """Разбить набор объектов на страницы."""
    from django.core.paginator import Paginator

    return Paginator(queryset, POSTS_PER_PAGE).get_page(
        request.GET.get('page')
    )


def index(request):
    """Показать ленту публикаций."""
    return render(
        request,
        'blog/index.html',
        {'page_obj': paginate(request, public_posts())},
    )


def category_posts(request, category_slug):
    """Показать публикации опубликованной категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = public_posts().filter(category=category)
    return render(
        request,
        'blog/category.html',
        {'category': category, 'page_obj': paginate(request, posts)},
    )


def profile(request, username):
    """Показать профиль и публикации пользователя."""
    profile_user = get_object_or_404(User, username=username)
    posts = post_queryset().filter(author=profile_user)
    if request.user != profile_user:
        posts = posts.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
    return render(
        request,
        'blog/profile.html',
        {
            'profile': profile_user,
            'page_obj': paginate(request, posts),
        },
    )


def post_detail(request, post_id):
    """Показать публикацию и комментарии."""
    posts = post_queryset()
    if not request.user.is_authenticated:
        posts = posts.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
    else:
        posts = posts.filter(
            Q(author=request.user)
            | Q(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now(),
            )
        )
    post = get_object_or_404(posts, pk=post_id)
    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'comments': post.comments.select_related('author'),
            'form': CommentForm(),
        },
    )


@login_required
def create_post(request):
    """Создать публикацию."""
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


def author_post(request, post_id):
    """Получить публикацию автора или перенаправить постороннего."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return None, redirect('blog:post_detail', post_id=post_id)
    return post, None


@login_required
def edit_post(request, post_id):
    """Изменить свою публикацию."""
    post, denied = author_post(request, post_id)
    if denied:
        return denied
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Удалить свою публикацию после подтверждения."""
    post, denied = author_post(request, post_id)
    if denied:
        return denied
    form = PostForm(instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'form': form})


@login_required
def add_comment(request, post_id):
    """Добавить комментарий к существующей публикации."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


def author_comment(request, post_id, comment_id):
    """Получить комментарий автора в заданной публикации."""
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )
    if comment.author != request.user:
        return None, redirect('blog:post_detail', post_id=post_id)
    return comment, None


@login_required
def edit_comment(request, post_id, comment_id):
    """Изменить свой комментарий."""
    comment, denied = author_comment(request, post_id, comment_id)
    if denied:
        return denied
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment},
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удалить свой комментарий после подтверждения."""
    comment, denied = author_comment(request, post_id, comment_id)
    if denied:
        return denied
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': comment},
    )


@login_required
def edit_profile(request):
    """Изменить собственный профиль."""
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        user = form.save()
        return redirect('blog:profile', username=user.username)
    return render(request, 'blog/user.html', {'form': form})
