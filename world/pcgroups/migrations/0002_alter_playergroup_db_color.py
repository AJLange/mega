# Generated by Django 4.1.11 on 2023-09-25 02:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pcgroups", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="playergroup",
            name="db_color",
            field=models.CharField(blank=True, max_length=20, verbose_name="Color"),
        ),
    ]