# Generated by Django 2.1.5 on 2019-01-22 15:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("memberbox", "0002_auto_20190119_2113"),
    ]

    operations = [
        migrations.AlterField(
            model_name="memberbox",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
