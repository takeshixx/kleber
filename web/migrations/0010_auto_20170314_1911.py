# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-14 18:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_auto_20170307_2350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucher',
            name='code',
            field=models.TextField(),
        ),
    ]
