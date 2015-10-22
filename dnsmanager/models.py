import time
import socket
import re

import dns.resolver
import dns.zone

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string

from .settings import ZONE_DEFAULTS, DNS_MANAGER_NAMESERVERS


class IntegerRangeField(models.IntegerField):
    """ Allow limiting Integer fields """

    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)


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


def validate_hostname_exists(fqdn):
    """
    :param hostname: Is hostname valid
    :return: True, or ValidationError
    """
    # Check hostname exists
    try:
        socket.gethostbyname(fqdn)
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
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$|\*", re.IGNORECASE)
    if not all(allowed.match(x) for x in hostname.split(".")):
        raise ValidationError('Hostname is not valid.')


def validate_service_record_data(data):
    # valid _sip._tls
    # invalid _sip._tls.
    # invalid sip.tls.
    # (\.[\w\d\.-]+\.)
    regex = re.compile(r'_[a-z\d-]{1,63}\._[a-z\d-]{1,63}?$', re.IGNORECASE)
    m = regex.match(data)
    if m is not None:
        return True
    else:
        raise ValidationError('Service record is not valid.')


class Zone(DateMixin):
    domain = models.OneToOneField('.'.join(settings.DNS_MANAGER_DOMAIN_MODEL.split('.')[-2:]))
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

    def clear_cache(self):
        try:
            return cache.delete_pattern("%s_*" % self.domain_name)
        except AttributeError:
            return False

    def delete(self, *args, **kwargs):
        self.clear_cache()
        super(Zone, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # increment serial on save
        serial_now = int(time.strftime('%Y%m%d00'))
        if self.serial < serial_now:
            self.serial = serial_now
        else:
            self.serial += 1
        self.clear_cache()
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

    @property
    def domain_name(self):
        return str(self.domain)

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
            # Validate that a / cname conflict does not occur
            for a_record in self.addressrecord_set.all():
                if self.canonicalnamerecord_set.filter(data=a_record.data).exists():
                    raise ValidationError('Cannot have CNAME and A records with same hostname.')
        except ObjectDoesNotExist:
            # In case that related record fails to validate
            pass
        try:
            # Validate by loading with Python DNS
            self.get_zone()
        except Exception as e:
            raise ValidationError('Failed to parse zone file with: %s' % str(e))

    def is_valid(self):
        key = '%s_validation' % (self.domain_name)
        data = cache.get(key, None)
        if data is None:
            try:
                self.validate()
            except ValidationError:
                data = False
            else:
                data = True
        cache.set(key, data, None)
        return data
    is_valid.boolean = True  # Attribute for django admin (makes for pretty icons)

    def check_delegation(self):
        try:
            answers = dns.resolver.query(self.domain_name, 'NS')
            for rdata in answers:
                if str(rdata).lower() not in DNS_MANAGER_NAMESERVERS:
                    raise ValidationError('Zone nameserver %s is not in DNS_MANAGER_NAMESERVERS' % str(rdata))
            if len(answers) <= 1:
                raise ValidationError('Zone has insufficient nameservers count: %s' % len(answers))
        except Exception as e:
            raise ValidationError('Exception during delegation check: %s' % str(e))

    def is_delegated(self):
        key = '%s_delegation' % (self.domain_name)
        data = cache.get(key, None)
        if data is None:
            try:
                self.check_delegation()
            except ValidationError:
                data = False
            else:
                data = True
        cache.set(key, data, None)
        return data
    is_delegated.boolean = True  # Attribute for django admin (makes for pretty icons)

    def render(self):
        """
        :return: Render the zone to a Bind zone string
        """
        return render_to_string('dnsmanager/zone_detail.txt', {'object': self})

    def update_from_text(self, text, partial=False):
        text = str(text.replace('\r\n', '\n'))  # DOS 2 Unix
        try:
            bind_zone = dns.zone.from_text(text=text, origin=self.domain.name, check_origin=False, relativize=True)
        except (AttributeError, dns.exception.SyntaxError) as e:
            return False, 'Zone Update Failed: %s' % str(e)

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

        for (name, ttl, rdata) in bind_zone.iterate_rdatas('SRV'):
            r, c = ServiceRecord.objects.get_or_create(zone=self,
                                                       data=name.to_text(),
                                                       target=rdata.target.to_text(),
                                                       port=int(rdata.port),
                                                       weight=int(rdata.weight),
                                                       priority=rdata.priority)
            r.ttl = int(ttl)
            r.save()

        return True, 'Zone Update Successful'


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
            return '%s.%s.' % (self.data, self.zone.domain)


class AddressRecord(BaseZoneRecord):

    ip = models.GenericIPAddressField(help_text="IP Address")

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

    @property
    def fq_target(self):
        if self.target.endswith('.'):
            return self.target
        else:
            return '%s.%s.' % (self.target, self.zone.domain)

    def clean(self):
        validate_hostname_string(self.data)
        validate_hostname_string(self.target)
        validate_hostname_exists(self.fq_target)


class MailExchangeRecord(BaseZoneRecord):

    priority = IntegerRangeField(min_value=0, max_value=65535, help_text="Priority")

    class Meta:
        db_table = 'dns_mailexchangerecord'
        unique_together = [('zone', 'data')]
        ordering = ['priority', 'data']

    def __unicode__(self):
        return "%s [%s: %s]" % (self.zone, self.priority, self.data)

    def clean(self):
        validate_hostname_string(self.data)
        validate_hostname_exists(self.fq_data)


class NameServerRecord(BaseZoneRecord):

    # FIXME: this record only valid for base zone, not subzone (maybe we want this)

    class Meta:
        db_table = 'dns_nameserverrecord'
        unique_together = [('zone', 'data')]

    def __unicode__(self):
        return "%s %s" % (self.zone, self.data)

    def clean(self):
        validate_hostname_exists(self.fq_data)


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


class ServiceRecord(BaseZoneRecord):
    priority = IntegerRangeField(min_value=0, max_value=65535, help_text="Priority")
    weight = IntegerRangeField(min_value=0, max_value=65535, help_text="Weight")
    port = IntegerRangeField(min_value=1, max_value=65535, help_text="TCP / UDP Port")
    target = models.CharField(max_length=128, help_text="Target")

    class Meta:
        db_table = 'dns_servicerecord'
        unique_together = [('zone', 'data', 'target')]

    def __unicode__(self):
        return "%s.%s -srv-> %s" % (self.data, self.zone, self.target)

    def clean(self):
        validate_service_record_data(self.data)
