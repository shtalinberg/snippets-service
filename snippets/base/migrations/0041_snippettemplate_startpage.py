# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-15 04:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_auto_20180607_1245'),
    ]

    operations = [
        migrations.AddField(
            model_name='snippettemplate',
            name='startpage',
            field=models.SmallIntegerField(default=4),
        ),
    ]