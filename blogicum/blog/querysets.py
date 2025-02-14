from django.db.models import Count
from django.db import models
from django.utils import timezone


class PostManager(models.Manager):

    def get_posts(
        self,
        is_published=True,
        select_related=True,
        comment_count=True
    ):
        posts = self
        if is_published:
            posts = posts.filter(
                pub_date__lt=timezone.now(),
                is_published=True,
                category__is_published=True
            )
        if select_related:
            posts = posts.select_related(
                'location',
                'category',
                'author'
            )
        if comment_count:
            posts = posts.annotate(
                comment_count=Count('comments')
            ).order_by(*self.model._meta.ordering)
        return posts
