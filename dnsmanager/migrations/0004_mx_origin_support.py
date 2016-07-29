# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnsmanager', '0003_ns_origin_support'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailexchangerecord',
            name='origin',
            field=models.CharField(default=b'@', help_text=b'MX Origin', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='mailexchangerecord',
            unique_together=set([('zone', 'data', 'origin')]),
        ),
    ]
