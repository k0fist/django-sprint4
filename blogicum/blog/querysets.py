from django.db import models
from django.utils import timezone


class PostManager(models.Manager):

    def published(self):
        return self.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True)
