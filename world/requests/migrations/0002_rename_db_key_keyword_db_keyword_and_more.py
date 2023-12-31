# Generated by Django 4.1.10 on 2023-11-14 21:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="keyword",
            old_name="db_key",
            new_name="db_keyword",
        ),
        migrations.RemoveField(
            model_name="keyword",
            name="db_file",
        ),
        migrations.AddField(
            model_name="file",
            name="db_keywords",
            field=models.ManyToManyField(blank=True, to="requests.keyword"),
        ),
    ]
