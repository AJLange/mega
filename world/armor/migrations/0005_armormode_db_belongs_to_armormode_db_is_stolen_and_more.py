# Generated by Django 4.1.10 on 2024-03-06 19:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("armor", "0004_alter_armormode_db_primary_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="armormode",
            name="db_belongs_to",
            field=models.CharField(
                default="None", max_length=255, verbose_name="Belongs to"
            ),
        ),
        migrations.AddField(
            model_name="armormode",
            name="db_is_stolen",
            field=models.BooleanField(default=False, verbose_name="Is Stolen?"),
        ),
        migrations.AddField(
            model_name="armormode",
            name="db_time_out",
            field=models.DateTimeField(blank=True, null=True, verbose_name="time out"),
        ),
    ]