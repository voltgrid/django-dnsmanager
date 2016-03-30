# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnsmanager', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='canonicalnamerecord',
            unique_together=set([('zone', 'data')]),
        ),
    ]
