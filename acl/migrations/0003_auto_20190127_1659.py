# Generated by Django 2.1.5 on 2019-01-27 15:59

from django.db import migrations

import acl.models


class Migration(migrations.Migration):
    dependencies = [
        ("acl", "0002_auto_20190119_2113"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalmachine",
            name="node_machine_name",
            field=acl.models.NodeField(
                blank=True,
                help_text="Name of device or machine used by the node",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="historicalmachine",
            name="node_name",
            field=acl.models.NodeField(
                blank=True, help_text="Name of the controlling node", max_length=20
            ),
        ),
        migrations.AddField(
            model_name="machine",
            name="node_machine_name",
            field=acl.models.NodeField(
                blank=True,
                help_text="Name of device or machine used by the node",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="machine",
            name="node_name",
            field=acl.models.NodeField(
                blank=True, help_text="Name of the controlling node", max_length=20
            ),
        ),
    ]
