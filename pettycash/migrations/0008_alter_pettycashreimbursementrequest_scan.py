# Generated by Django 3.2.7 on 2022-10-26 10:31

import dynamic_filenames
import stdimage.models
import stdimage.validators
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pettycash", "0007_alter_pettycashreimbursementrequest_scan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pettycashreimbursementrequest",
            name="scan",
            field=stdimage.models.StdImageField(
                blank=True,
                help_text="Scan, photo or similar of the receipt",
                null=True,
                upload_to=dynamic_filenames.FilePattern(
                    filename_pattern="{app_label:.25}/{model_name:.30}/{uuid:base32}{ext}"
                ),
                validators=[
                    stdimage.validators.MinSizeValidator(100, 100),
                    stdimage.validators.MaxSizeValidator(8000, 8000),
                ],
            ),
        ),
    ]