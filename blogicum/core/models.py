from django.db import models


class BaseModel(models.Model):
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


class HeaderBaseModel(BaseModel):
    """
    Абстрактная модель.

    Добавляет в абстрактный базовый модуль поле 'Заголовок'.
    """

    title = models.CharField('Заголовок', max_length=256)

    class Meta:
        abstract = True
