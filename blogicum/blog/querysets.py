from django.db.models import Count
from django.db import models
from django.utils import timezone


class PostManager(models.Manager):

    def published(self, filter_date=True, filter_category=True):
        queryset = self.all()

        if filter_date:
            queryset = queryset.filter(pub_date__lt=timezone.now())

        if filter_category:
            queryset = queryset.filter(
                is_published=True,
                category__is_published=True
            )
        return queryset.select_related(
            'location',
            'category',
            'author'
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
