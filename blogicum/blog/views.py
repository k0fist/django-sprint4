from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .models import Post, Category, User, Comment
from .forms import PostForm, CommentForm, CustomUserChangeForm


MAX_POSTS = 10


class AuthorPostMixin:
    """Миксин для проверки авторства поста."""

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return HttpResponseRedirect(
                reverse_lazy('blog:post_detail', kwargs={'pk': post.pk})
            )
        return super().dispatch(request, *args, **kwargs)


class AuthorCommentMixin:
    """Миксин для проверки авторства комментариев."""

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для проверки авторства для входа в профиль."""

    def test_func(self):
        object = self.get_object()
        return object == self.request.user


class AllPostMixin():
    """Миксин для всех действй с постами."""

    model = Post


class AllCommentMixin():
    """Миксин для всех действий с комментариями."""

    model = Comment
    template_name = 'blog/add_comment.html'


class CreateUpdateCommentMixin(AllCommentMixin):
    """Миксин для создания и редактирования комментария."""

    form_class = CommentForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'pk': self.kwargs['post_pk']}
        )


class ProfileUserView(DetailView):
    """CBV для открытия профиля."""

    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    paginate_by = MAX_POSTS

    def get_object(self, queryset=None):
        try:
            return User.objects.get(username=self.kwargs['slug'])
        except User.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        posts = Post.objects.filter(author=user)
        if self.request.user != user:
            posts = posts.filter(is_published=True)
        paginator = Paginator(posts, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['profile'] = user
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """CBV для редактирования профиля."""

    model = User
    form_class = CustomUserChangeForm
    template_name = 'blog/edit_profile.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'slug': self.request.user.username}
        )


class PostListView(AllPostMixin, ListView):
    """CBV для страницы с постами."""

    queryset = Post.objects.published().select_related(
        'location',
        'category',
        'author'
    )
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = MAX_POSTS


class PostDetailView(AllPostMixin, DetailView):
    """CBV для просмотра страницы поста."""

    template_name = 'blog/post_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        if not post.is_published:
            if post.author != self.request.user:
                raise Http404()
        context['form'] = CommentForm()
        context['comments'] = self.object.comment.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, AllPostMixin, CreateView):
    """CBV для создания поста."""

    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'slug': self.request.user.username}
        )


class PostUpdateView(AuthorPostMixin, AllPostMixin, UpdateView):
    """CBV для редактирования поста."""

    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.pk}
        )

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['post_pk'])


class PostDeleteView(AuthorPostMixin, AllPostMixin, DeleteView):
    """CBV для удаления поста."""

    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['post_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        form = PostForm(instance=post)
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return redirect(reverse_lazy('blog:index'))


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

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs['comment_pk'])


class CommentDeleteView(AuthorCommentMixin, AllCommentMixin, DeleteView):
    """CBV для удаления комментария."""

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        comment = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_pk'],
            post=post
        )
        return comment

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return redirect(reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': comment.post.pk})
        )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = category.posts.published()
    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category,
    }
    return render(request, 'blog/category.html', context)
