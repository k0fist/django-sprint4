from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.db.models import Count
from .models import Post, Category, User, Comment
from .forms import CommentForm, PostForm, MyUserChangeForm


MAX_POSTS = 10


def paginate_posts(request, posts, paginate_by):
    """Функция для пагинации постов."""
    paginator = Paginator(posts, paginate_by)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


class AuthorPostMixin:
    """Миксин для проверки авторства поста."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect(
                reverse('blog:post_detail', args=[post.pk])
            )
        return super().dispatch(request, *args, **kwargs)


class AuthorCommentMixin:
    """Миксин для проверки авторства комментариев."""

    def dispatch(self, request, *args, **kwargs):
        comments = self.get_object()
        if comments.author != request.user:
            print(kwargs)
            return redirect(
                reverse(
                    'blog:post_detail',
                    kwargs={'post_pk': self.kwargs['post_pk']})
            )
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
        print(self.kwargs['post_pk'])
        return reverse('blog:post_detail', args=[self.kwargs['post_pk']])


class ProfileUserView(DetailView):
    """CBV для открытия профиля."""

    model = User
    template_name = 'blog/profile.html'
    paginate_by = MAX_POSTS

    def get_object(self, user_queryset=None):
        try:
            return User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist:
            raise get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        if self.request.user == author:
            posts = author.posts.all().order_by(
                '-pub_date'
            ).annotate(comment_count=Count('comments'))
        else:
            posts = author.posts.published().order_by(
                '-pub_date'
            ).annotate(comment_count=Count('comments'))
        context['profile'] = author
        context['page_obj'] = paginate_posts(
            self.request,
            posts,
            self.paginate_by
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """CBV для редактирования профиля."""

    model = User
    form_class = MyUserChangeForm
    template_name = 'blog/edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostListView(ListView):
    """CBV для страницы с постами."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = MAX_POSTS

    def get_queryset(self):
        queryset = Post.objects.published().order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostDetailView(DetailView):
    """CBV для просмотра страницы поста."""

    model = Post
    template_name = 'blog/post_detail.html'
    posts = Post.objects.annotate(comment_count=Count('comments'))

    def get_object(self):
        pk = self.kwargs.get('post_pk')
        return get_object_or_404(Post, pk=pk)

    def get_post(self):
        post = self.get_object()
        if not post.is_published and post.author != self.request.user:
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        context['post'] = self.get_post()
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

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_pk']])


class PostDeleteView(AuthorPostMixin, DeleteView):
    """CBV для удаления поста."""

    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        form = PostForm(instance=post)
        context['form'] = form
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
        comment = self.get_object()  # Получаем объект комментария
        return reverse('blog:post_detail', kwargs={'post_pk': comment.post.pk})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = category.posts.published_for_category(
        category
    ).order_by('-pub_date').annotate(comment_count=Count('comments'))
    context = {
        'page_obj': paginate_posts(request, posts, MAX_POSTS),
        'category': category,
    }
    return render(request, 'blog/category.html', context)
