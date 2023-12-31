# Generated by Django 4.1.10 on 2023-11-15 21:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0003_delete_file_delete_keyword_delete_topic"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="db_is_archived",
            field=models.BooleanField(default=False, verbose_name="Archived"),
        ),
        migrations.AddField(
            model_name="request",
            name="db_is_dead",
            field=models.BooleanField(default=False, verbose_name="Deleted"),
        ),
    ]
