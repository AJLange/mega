# Generated by Django 4.1.10 on 2023-08-12 00:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("objects", "0014_defaultobject_defaultcharacter_defaultexit_and_more"),
        ("pcgroups", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BulletinBoard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "db_name",
                    models.CharField(max_length=120, verbose_name="Board Name"),
                ),
                (
                    "db_date_created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="date created"
                    ),
                ),
                (
                    "db_timeout",
                    models.IntegerField(
                        blank=True, default=180, verbose_name="Timeout"
                    ),
                ),
                (
                    "db_groups",
                    models.ManyToManyField(blank=True, to="pcgroups.playergroup"),
                ),
                (
                    "has_subscriber",
                    models.ManyToManyField(blank=True, to="objects.objectdb"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BoardPost",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "db_title",
                    models.CharField(max_length=360, verbose_name="Post Title"),
                ),
                (
                    "db_date_created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="date created"
                    ),
                ),
                ("posted_by", models.CharField(max_length=120, verbose_name="Author")),
                ("body_text", models.TextField(verbose_name="Post")),
                (
                    "db_board",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="boards.bulletinboard",
                    ),
                ),
                ("read_by", models.ManyToManyField(blank=True, to="objects.objectdb")),
            ],
        ),
    ]
