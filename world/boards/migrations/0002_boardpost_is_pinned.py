# Generated by Django 4.1.10 on 2024-03-06 19:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("boards", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="boardpost",
            name="is_pinned",
            field=models.BooleanField(default=False, verbose_name="Is Pinned?"),
        ),
    ]