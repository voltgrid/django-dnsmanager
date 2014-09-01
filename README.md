# DNS Manager for Django

Reusable Django app that provides DNS Zone editing and management.

This is used by [Volt Grid](https://www.voltgrid.com/).

[![Build Status](https://travis-ci.org/voltgrid/django-dnsmanager.svg?branch=master)](https://travis-ci.org/voltgrid/django-dnsmanager)

## Features

* Import & Export Bind zone files
* Zone list generation
* Zone validation
* Recipe based zone updates (eg one click add Google Apps MX / Cname records)
* Easily integrate with Bind
* Zone versioning using Django Reversion

## Installation

Add to your Django project in your Python path.

Add `dnsmanager` to your `INSTALLED_APPS`.

Set `DNS_MANAGER_DOMAIN_MODEL` in `settings.py`. This must point to a model that provides a _name_ field. Eg:

    class Domain(models.Model):
    
        user = models.ForeignKey(User, related_name='domains')
        name = models.CharField(max_length=253, unique=True, help_text='Domain Name')
    
        class Meta:
            ordering = ['name']
    
        def __unicode__(self):
            return "%s" % self.name
            
Run `manage.py syncdb`.
