# Generated by Django 2.2.5 on 2019-09-29 12:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0010_auditrecord_historicalauditrecord"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicaluser",
            name="phone_number",
            field=models.CharField(
                blank=True,
                help_text="Optional; only visible to the trustees and board delegated administrators",
                max_length=40,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered with country code (+31, etc.) and no spaces, dashes, etc.",
                        regex="^\\+\\d{9,15}$",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True,
                help_text="Optional; only visible to the trustees and board delegated administrators",
                max_length=40,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be entered with country code (+31, etc.) and no spaces, dashes, etc.",
                        regex="^\\+\\d{9,15}$",
                    )
                ],
            ),
        ),
    ]
