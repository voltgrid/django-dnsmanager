import time
import socket
import re

import dns.zone

from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string

from .settings import ZONE_DEFAULTS


class DateMixin(models.Model):
    """ Model Mixin to add modification and creation datestamps """
    created = models.DateTimeField("Date Created", auto_now_add=True)
    updated = models.DateTimeField("Date Updated", auto_now=True)

    version = models.IntegerField(default=0, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # increment version on save
        self.version += 1
        super(DateMixin, self).save(*args, **kwargs)


def validate_hostname_exists(hostname, domain):
    """
    :param hostname: Is hostname valid
    :return: True, or ValidationError
    """
    # Check hostname exists
    try:
        if hostname.endswith('.'):
            socket.gethostbyname(hostname)
        else:
            socket.gethostbyname('%s.%s' % (hostname, domain))
        return True
    except socket.error:
        raise ValidationError('Hostname does not exist.')


def validate_hostname_string(hostname):
    """
    :param hostname: Is hostname valid
    :return: True, or ValidationError
    """
    # More complete validation here http://en.wikipedia.org/wiki/Hostname#Restrictions_on_valid_host_names
    if hostname == "@":
        return True
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if not all(allowed.match(x) for x in hostname.split(".")):
        raise ValidationError('Hostname is not valid.')

from test_app.models import Domain
class Zone(DateMixin):

    #domain = models.ForeignKey(settings.DNS_MANAGER_DOMAIN_MODEL.split('.', 1)[-1], primary_key=True)
    domain = models.ForeignKey(Domain, primary_key=True)
    soa_email = models.CharField(max_length=128, default=ZONE_DEFAULTS['soa'])
    serial = models.PositiveIntegerField(default=0)
    refresh = models.PositiveIntegerField(default=ZONE_DEFAULTS['refresh'])
    retry = models.PositiveIntegerField(default=ZONE_DEFAULTS['retry'])
    expire = models.PositiveIntegerField(default=ZONE_DEFAULTS['expire'])
    minimum = models.PositiveIntegerField(default=ZONE_DEFAULTS['minimum'], help_text="nxdomain ttl, bind9+")
    ttl = models.PositiveIntegerField(default=ZONE_DEFAULTS['ttl'], help_text='Default record TTL')

    class Meta:
        db_table = 'dns_zone'
        ordering = ['domain']
        permissions = (
            ("view_zones", "Can view zones"),
        )

    def __unicode__(self):
        return "%s [%s]" % (self.domain, self.serial)

    def save(self, *args, **kwargs):
        # increment serial on save
        serial_now = int(time.strftime('%Y%m%d00'))
        if self.serial < serial_now:
            self.serial = serial_now
        else:
            self.serial += 1
        super(Zone, self).save(*args, **kwargs)

    @property
    def description(self):
        return 'Hosted DNS Zone (%s)' % self.domain

    @property
    def owner_src(self):
        return self.domain.owner_src

    @property
    def rname(self):
        return self.soa_email.replace('@', '.')

    def get_absolute_url(self):
        return reverse('zone_detail', kwargs={'pk': self.pk, })

    def get_zone(self):
        return dns.zone.from_text(str(self.render()), origin=str(self.domain), check_origin=True, relativize=True)

    def validate(self):
        try:
            # Can't run this on clean due to relation not being saved.. need a custom method.
            if self.nameserverrecord_set.count() < 2:
                raise ValidationError('You must assign at least two name servers.')
            if self.addressrecord_set.count() < 1:
                raise ValidationError('You must assign at least one address record.')
        except ObjectDoesNotExist:
            # In case that related record fails to validate
            pass
        try:
            # Validate by loading with Python DNS
            self.get_zone()
        except Exception as e:
            raise ValidationError('Failed to parse zone file with: %s' % str(e))

    def is_valid(self):
        try:
            self.validate()
        except ValidationError:
            return False
        else:
            return True
    is_valid.boolean = True  # Attribute for django admin (makes for pretty icons)

    def render(self):
        """
        :return: Render the zone to a Bind zone string
        """
        return render_to_string('dnsmanager/zone_detail.txt', {'object': self})

    def update_from_text(self, text, partial=False):
        text = str(text.replace('\r\n', '\n'))  # DOS 2 Unix
        try:
            bind_zone = dns.zone.from_text(text=text, origin=self.domain.name, check_origin=False, relativize=True)
        except dns.exception.SyntaxError:
            return False

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('SOA'):  # should only be one
            self.expire = rdata.expire
            self.minimum = rdata.minimum
            self.refresh = rdata.refresh
            self.retry = rdata.retry
            self.soa_email = str(rdata.rname).lower()
            self.serial = rdata.serial
        self.save()

        if not partial:
            self.addressrecord_set.all().delete()
            self.nameserverrecord_set.all().delete()
            self.mailexchangerecord_set.all().delete()
            self.canonicalnamerecord_set.all().delete()
            self.textrecord_set.all().delete()

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('A'):
            r, c = AddressRecord.objects.get_or_create(zone=self, data=str(name).lower(), ip=str(rdata))
            r.ttl = int(ttl)
            r.save()

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('NS'):
            r, c = NameServerRecord.objects.get_or_create(zone=self, data=str(rdata).lower())
            r.ttl = int(ttl)
            r.save()

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('MX'):
            r, c = MailExchangeRecord.objects.get_or_create(zone=self,
                                                            data=str(rdata.exchange).lower(),
                                                            priority=int(rdata.preference))
            r.save()

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('CNAME'):
            r, c = CanonicalNameRecord.objects.get_or_create(zone=self, data=str(name), target=str(rdata).lower())
            r.ttl = int(ttl)
            r.save()

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('TXT'):
            r, c = TextRecord.objects.get_or_create(zone=self, data=str(name), text=str(rdata))
            r.ttl = int(ttl)
            r.save()

        return True


class BaseZoneRecord(DateMixin):

    zone = models.ForeignKey(Zone)
    data = models.CharField(max_length=255, help_text="Data")

    ttl = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        # order_with_respect_to = 'zone'
        abstract = True

    def __unicode__(self):
        return "%s [%s]" % (self.zone, self.data)

    # Override TTL with default
    @property
    def ttlx(self):
        if self.ttl is not None:
            return self.ttl
        else:
            return self.zone.ttl

    @property
    def fq_data(self):
        if self.data.endswith('.'):
            return self.data
        else:
            return '%s.%s' % (self.data, self.zone.domain)


class AddressRecord(BaseZoneRecord):

    ip = models.IPAddressField(help_text="IP Address")

    class Meta:
        db_table = 'dns_addressrecord'
        unique_together = [('zone', 'data', 'ip')]

    def __unicode__(self):
        return "%s.%s -> %s" % (self.data, self.zone, self.ip)

    def clean(self):
        validate_hostname_string(self.data)


class CanonicalNameRecord(BaseZoneRecord):

    target = models.CharField(max_length=128, help_text="Target")

    class Meta:
        db_table = 'dns_canonicalnamerecord'
        unique_together = [('zone', 'data', 'target')]

    def __unicode__(self):
        return "%s.%s -> %s" % (self.data, self.zone, self.target)

    def clean(self):
        validate_hostname_string(self.data)
        validate_hostname_exists(self.target, self.zone.domain)


class MailExchangeRecord(BaseZoneRecord):

    priority = models.IntegerField(max_length=3, help_text="Priority")

    class Meta:
        db_table = 'dns_mailexchangerecord'
        unique_together = [('zone', 'data')]
        ordering = ['priority', 'data']

    def __unicode__(self):
        return "%s [%s: %s]" % (self.zone, self.priority, self.data)

    def clean(self):
        validate_hostname_string(self.data)
        validate_hostname_exists(self.fq_data, self.zone.domain)


class NameServerRecord(BaseZoneRecord):

    # FIXME: this record only valid for base zone, not subzone (maybe we want this)

    class Meta:
        db_table = 'dns_nameserverrecord'
        unique_together = [('zone', 'data')]

    def __unicode__(self):
        return "%s %s" % (self.zone, self.data)

    def clean(self):
        validate_hostname_exists(self.fq_data, self.zone.domain)


class TextRecord(BaseZoneRecord):

    text = models.CharField(max_length=255, help_text="Text")

    class Meta:
        db_table = 'dns_textrecord'

    def __unicode__(self):
        return "%s [%s]" % (self.zone, self.text)

    def clean(self):
        if not (self.text.startswith('"') and self.text.endswith('"')):
            raise ValidationError('Record must begin and end with double quotes.')
        if not self.text.count('"') == 2:
            raise ValidationError('Record must not contain more than 2 quotes.')
