from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserChangeForm
from .models import Post, Category, User, Comment
from django.http import HttpResponseRedirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from .forms import CustomUserChangeForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .forms import PostForm, CommentForm


MAX_POSTS = 5


class PostListView(ListView):
    model = Post
    queryset = Post.objects.published().select_related(
        'location',
        'category',
        'author'
    )
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = MAX_POSTS


class ProfileUserView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['profile'] = user
        context['page_obj'] = Post.objects.filter(
            author=user,
            is_published=True
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'blog/edit_profile.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        return self.request.user


class PostDetailView(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Записываем в переменную form пустой объект формы.
        context['form'] = CommentForm()
        # Запрашиваем все поздравления для выбранного дня рождения.
        context['comments'] = (
            # Дополнительно подгружаем авторов комментариев,
            # чтобы избежать множества запросов к БД.
            self.object.comment.select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        # Присвоить полю author объект пользователя из запроса.
        form.instance.author = self.request.user
        # Продолжить валидацию, описанную в форме.
        response = super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.pk}
        )


class PostDeleteView(DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    post = None
    model = Comment
    form_class = CommentForm

    # Переопределяем dispatch()
    def dispatch(self, request, *args, **kwargs):
        self.post = get_object_or_404(Post, pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    # Переопределяем form_valid()
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post
        return super().form_valid(form)

    # Переопределяем get_success_url()
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk})


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = PostForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.pk}
        )
    
    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs['comment_pk'])


class CommentDeleteView(DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, pk=self.kwargs['comment_pk'])


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = category.posts.published()
    context = {
        'page_obj': posts,
        'category': category,
    }
    return render(request, 'blog/category.html', context)

