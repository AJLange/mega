# Generated by Django 4.1.10 on 2023-11-15 21:59

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0005_remove_request_db_is_archived"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="request",
            name="db_is_dead",
        ),
    ]