# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dnsmanager', '0002_canonicalnamerecord_unique'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='addressrecord',
            options={'ordering': ['data']},
        ),
        migrations.AlterModelOptions(
            name='canonicalnamerecord',
            options={'ordering': ['data']},
        ),
        migrations.AlterModelOptions(
            name='nameserverrecord',
            options={'ordering': ['data']},
        ),
        migrations.AlterModelOptions(
            name='servicerecord',
            options={'ordering': ['data', 'priority', 'target']},
        ),
        migrations.AlterModelOptions(
            name='textrecord',
            options={'ordering': ['data', 'text']},
        ),
        migrations.AddField(
            model_name='nameserverrecord',
            name='origin',
            field=models.CharField(default=b'@', help_text=b'NS Origin', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='nameserverrecord',
            unique_together=set([('zone', 'data', 'origin')]),
        ),
    ]
