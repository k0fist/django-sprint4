from django.db import models
from django.contrib.auth import get_user_model
from blog.querysets import PostManager


User = get_user_model()


class PublishedAndDateBaseModel(models.Model):
    """
    Абстрактная модель.

    Добавляет флаг is_published и дату создания поста.
    """

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class Category(PublishedAndDateBaseModel):

    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL;'
                  ' разрешены символы латиницы,'
                  ' цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title',)

    def __str__(self):
        return self.title[:50]


class Location(PublishedAndDateBaseModel):
    name = models.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name',)

    def __str__(self):
        return self.name[:50]


class Post(PublishedAndDateBaseModel):

    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем'
                  ' — можно делать отложенные публикации.'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    objects = PostManager()

    class Meta:
        default_related_name = 'posts'
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title[:50]


class Comment(models.Model):
    text = models.TextField('Текст')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
    )
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )

    class Meta:
        default_related_name = 'comments'
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return self.text[:50]
