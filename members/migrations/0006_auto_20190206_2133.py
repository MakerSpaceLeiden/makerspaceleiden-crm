# Generated by Django 2.1.5 on 2019-02-06 20:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0005_auto_20190206_1415"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicaltag",
            name="tag",
            field=models.CharField(db_index=True, max_length=30),
        ),
        migrations.AlterField(
            model_name="tag",
            name="tag",
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
