# Generated by Django 4.1.10 on 2023-11-15 21:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0004_request_db_is_archived_request_db_is_dead"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="request",
            name="db_is_archived",
        ),
    ]