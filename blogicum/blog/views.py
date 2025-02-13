from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from django.core.paginator import Paginator
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .models import Post, Category, User, Comment
from .forms import CommentForm, PostForm, BlogicumUserChangeForm


MAX_POSTS = 10


def get_paginated_posts(request, posts, paginate_by=MAX_POSTS):
    """Функция для пагинации постов."""
    return Paginator(posts, paginate_by).get_page(request.GET.get('page'))


class AuthorPostMixin:
    """Миксин для проверки авторства поста."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', self.kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)


class AuthorCommentMixin:
    """Миксин для проверки авторства комментариев."""

    def dispatch(self, request, *args, **kwargs):
        comments = self.get_object()
        if comments.author != request.user:
            return redirect('blog:post_detail', self.kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для проверки авторства для входа в профиль."""

    def test_func(self):
        return self.get_object() == self.request.user


class MainCommentMixin():
    """Миксин для всех действий с комментариями."""

    model = Comment
    template_name = 'blog/add_comment.html'


class CreateUpdateCommentMixin(MainCommentMixin):
    """Миксин для создания и редактирования комментария."""

    form_class = CommentForm

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_pk']])


class ProfileUserView(DetailView):
    """CBV для открытия профиля."""

    model = User
    template_name = 'blog/profile.html'
    paginate_by = MAX_POSTS

    def get_object(self, user_queryset=None):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        context['profile'] = author
        context['page_obj'] = get_paginated_posts(
            self.request,
            author.posts.get_filtered_posts(author=author)
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """CBV для редактирования профиля."""

    model = User
    form_class = BlogicumUserChangeForm
    template_name = 'blog/edit_profile.html'

    def get_object(self, user_queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostListView(ListView):
    """CBV для страницы с постами."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = MAX_POSTS

    def get_queryset(self):
        return Post.objects.get_filtered_posts()


class PostDetailView(DetailView):
    """CBV для просмотра страницы поста."""

    model = Post
    template_name = 'blog/post_detail.html'

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        if self.request.user == post.author:
            return post
        # if not post.is_published:
        #     raise Http404
        return get_object_or_404(Post.objects.get_filtered_posts(
            select_related=False,
            comment_count=False,
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        context['post'] = self.object
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """CBV для создания поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


class PostUpdateView(AuthorPostMixin, UpdateView):
    """CBV для редактирования поста."""

    form_class = PostForm
    pk_url_kwarg = 'post_pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class PostDeleteView(AuthorPostMixin, DeleteView):
    """CBV для удаления поста."""

    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class CommentCreateView(
        LoginRequiredMixin,
        CreateUpdateCommentMixin,
        CreateView):
    """CBV для создания комментария."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        return super().form_valid(form)


class CommentUpdateView(
        AuthorCommentMixin,
        CreateUpdateCommentMixin,
        UpdateView):
    """CBV для редактирования комментария."""

    pk_url_kwarg = 'comment_pk'


class CommentDeleteView(AuthorCommentMixin, MainCommentMixin, DeleteView):
    """CBV для удаления комментария."""

    pk_url_kwarg = 'comment_pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    context = {
        'page_obj': get_paginated_posts(
            request,
            category.posts.get_filtered_posts()
        ),
        'category': category,
    }
    return render(request, 'blog/category.html', context)
