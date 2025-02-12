from django.db.models import Count
from django.db import models
from django.utils import timezone


class PostManager(models.Manager):

    def published(
        self,
        filter_category=True,
        select_related=True,
        comment_count=True,
        author=None
    ):
        post_queryset = self.filter(pub_date__lt=timezone.now())
        if filter_category:
            post_queryset = post_queryset.filter(
                is_published=True,
                category__is_published=True
            )
        if select_related:
            post_queryset = post_queryset.select_related(
                'location',
                'category',
                'author'
            )
        if comment_count:
            post_queryset = post_queryset.annotate(
                comment_count=Count('comments')
            )
        if author:
            post_queryset = post_queryset.filter(author=author)
        return post_queryset.order_by('-pub_date')
