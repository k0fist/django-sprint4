# Generated by Django 4.2.16 on 2025-02-06 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_alter_category_options_alter_location_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='image',
            field=models.ImageField(blank=True, upload_to='post_images', verbose_name='Фото'),
        ),
    ]
