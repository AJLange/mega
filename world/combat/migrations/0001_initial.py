# Generated by Django 4.1.10 on 2023-08-11 23:22

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BusterList",
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
                ("db_name", models.CharField(max_length=200, verbose_name="Name")),
                (
                    "db_class",
                    models.IntegerField(
                        choices=[
                            (1, "Ranged"),
                            (2, "Wave"),
                            (3, "Thrown"),
                            (4, "Melee"),
                            (5, "Blitz"),
                            (6, "Sneak"),
                            (7, "Grapple"),
                            (8, "Spell"),
                            (9, "Will"),
                            (10, "Gadget"),
                            (11, "Chip"),
                            (12, "Random"),
                        ]
                    ),
                ),
                (
                    "db_type_1",
                    models.IntegerField(
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ]
                    ),
                ),
                (
                    "db_type_2",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_type_3",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_flag_1",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Megablast"),
                            (2, "Exceed"),
                            (3, "Priority"),
                            (4, "Stable"),
                            (5, "Blind"),
                            (6, "Degrade"),
                            (7, "Entangle"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_flag_2",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Megablast"),
                            (2, "Exceed"),
                            (3, "Priority"),
                            (4, "Stable"),
                            (5, "Blind"),
                            (6, "Degrade"),
                            (7, "Entangle"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_thief",
                    models.CharField(max_length=100, verbose_name="Stolen By"),
                ),
                (
                    "db_date_created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="date swiped"
                    ),
                ),
                (
                    "db_time_out",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="time out"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="GenericAttack",
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
                ("db_name", models.CharField(max_length=200, verbose_name="Name")),
                (
                    "db_class",
                    models.IntegerField(
                        choices=[
                            (1, "Ranged"),
                            (2, "Wave"),
                            (3, "Thrown"),
                            (4, "Melee"),
                            (5, "Blitz"),
                            (6, "Sneak"),
                            (7, "Grapple"),
                            (8, "Spell"),
                            (9, "Will"),
                            (10, "Gadget"),
                            (11, "Chip"),
                            (12, "Random"),
                        ]
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Weapon",
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
                ("db_name", models.CharField(max_length=200, verbose_name="Name")),
                (
                    "db_class",
                    models.IntegerField(
                        choices=[
                            (1, "Ranged"),
                            (2, "Wave"),
                            (3, "Thrown"),
                            (4, "Melee"),
                            (5, "Blitz"),
                            (6, "Sneak"),
                            (7, "Grapple"),
                            (8, "Spell"),
                            (9, "Will"),
                            (10, "Gadget"),
                            (11, "Chip"),
                            (12, "Random"),
                        ]
                    ),
                ),
                (
                    "db_type_1",
                    models.IntegerField(
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ]
                    ),
                ),
                (
                    "db_type_2",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_type_3",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Slashing"),
                            (2, "Piercing"),
                            (3, "Electric"),
                            (4, "Explosive"),
                            (5, "Fire"),
                            (6, "Gravity"),
                            (7, "Air"),
                            (8, "Ice"),
                            (9, "Toxic"),
                            (10, "Blunt"),
                            (11, "Quake"),
                            (12, "Karate"),
                            (13, "Sonic"),
                            (14, "Time"),
                            (15, "Wood"),
                            (16, "Water"),
                            (17, "Plasma"),
                            (18, "Laser"),
                            (19, "Light"),
                            (20, "Darkness"),
                            (21, "Psycho"),
                            (22, "Chi"),
                            (23, "Disenchant"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_flag_1",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Megablast"),
                            (2, "Exceed"),
                            (3, "Priority"),
                            (4, "Stable"),
                            (5, "Blind"),
                            (6, "Degrade"),
                            (7, "Entangle"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_flag_2",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Megablast"),
                            (2, "Exceed"),
                            (3, "Priority"),
                            (4, "Stable"),
                            (5, "Blind"),
                            (6, "Degrade"),
                            (7, "Entangle"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "db_date_created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="date created"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
