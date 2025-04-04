# Generated by Django 3.1.2 on 2020-10-13 01:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0015_topicnote_type_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topicnote',
            name='topicId',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='noteTopic', to='main.topic'),
        ),
    ]
