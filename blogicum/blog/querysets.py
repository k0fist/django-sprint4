from django.db import models
from django.utils import timezone


class PostManager(models.Manager):

    def published(self):
        return self.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True
        ).select_related(
            'location',
            'category',
            'author')

    def published_for_category(self, category):
        """Возвращает опубликованные посты для конкретной категории."""
        return self.published().filter(category=category)
