# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import dnsmanager.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_auto_20151020_1226'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddressRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
                ('ip', models.GenericIPAddressField(help_text=b'IP Address')),
            ],
            options={
                'db_table': 'dns_addressrecord',
            },
        ),
        migrations.CreateModel(
            name='CanonicalNameRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
                ('target', models.CharField(help_text=b'Target', max_length=128)),
            ],
            options={
                'db_table': 'dns_canonicalnamerecord',
            },
        ),
        migrations.CreateModel(
            name='MailExchangeRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
                ('priority', dnsmanager.models.IntegerRangeField(help_text=b'Priority')),
            ],
            options={
                'ordering': ['priority', 'data'],
                'db_table': 'dns_mailexchangerecord',
            },
        ),
        migrations.CreateModel(
            name='NameServerRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'dns_nameserverrecord',
            },
        ),
        migrations.CreateModel(
            name='ServiceRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
                ('priority', dnsmanager.models.IntegerRangeField(help_text=b'Priority')),
                ('weight', dnsmanager.models.IntegerRangeField(help_text=b'Weight')),
                ('port', dnsmanager.models.IntegerRangeField(help_text=b'TCP / UDP Port')),
                ('target', models.CharField(help_text=b'Target', max_length=128)),
            ],
            options={
                'db_table': 'dns_servicerecord',
            },
        ),
        migrations.CreateModel(
            name='TextRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('data', models.CharField(help_text=b'Data', max_length=255)),
                ('ttl', models.PositiveIntegerField(null=True, blank=True)),
                ('text', models.CharField(help_text=b'Text', max_length=255)),
            ],
            options={
                'db_table': 'dns_textrecord',
            },
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'Date Updated')),
                ('version', models.IntegerField(default=0, editable=False)),
                ('soa_email', models.CharField(default=b'hostmaster', max_length=128)),
                ('serial', models.PositiveIntegerField(default=0)),
                ('refresh', models.PositiveIntegerField(default=28800)),
                ('retry', models.PositiveIntegerField(default=7200)),
                ('expire', models.PositiveIntegerField(default=2419200)),
                ('minimum', models.PositiveIntegerField(default=600, help_text=b'nxdomain ttl, bind9+')),
                ('ttl', models.PositiveIntegerField(default=3600, help_text=b'Default record TTL')),
                ('domain', models.OneToOneField(to='account.Domain')),
            ],
            options={
                'ordering': ['domain'],
                'db_table': 'dns_zone',
                'permissions': (('view_zones', 'Can view zones'),),
            },
        ),
        migrations.AddField(
            model_name='textrecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AddField(
            model_name='servicerecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AddField(
            model_name='nameserverrecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AddField(
            model_name='mailexchangerecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AddField(
            model_name='canonicalnamerecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AddField(
            model_name='addressrecord',
            name='zone',
            field=models.ForeignKey(to='dnsmanager.Zone'),
        ),
        migrations.AlterUniqueTogether(
            name='servicerecord',
            unique_together=set([('zone', 'data', 'target')]),
        ),
        migrations.AlterUniqueTogether(
            name='nameserverrecord',
            unique_together=set([('zone', 'data')]),
        ),
        migrations.AlterUniqueTogether(
            name='mailexchangerecord',
            unique_together=set([('zone', 'data')]),
        ),
        migrations.AlterUniqueTogether(
            name='canonicalnamerecord',
            unique_together=set([('zone', 'data', 'target')]),
        ),
        migrations.AlterUniqueTogether(
            name='addressrecord',
            unique_together=set([('zone', 'data', 'ip')]),
        ),
    ]
