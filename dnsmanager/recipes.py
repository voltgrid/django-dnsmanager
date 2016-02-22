from .models import AddressRecord
from .models import CanonicalNameRecord
from .models import MailExchangeRecord
from .models import NameServerRecord
from .models import TextRecord
from .models import ServiceRecord
from .settings import ZONE_DEFAULTS


class Recipe(object):
    """ Custom Zone Recipe """
    def __init__(self, zone):
        self.zone = zone

    def save(self):
        self.zone.save()


class NameServerRecipe(Recipe):
    """ Superclass for Name Server Recipe """
    data = None

    def __init__(self, zone):
        super(NameServerRecipe, self).__init__(zone)
        self.set_ns(self.data)

    def set_ns(self, data):
        if data is not None:
            # Remove existing NS
            NameServerRecord.objects.filter(zone=self.zone).delete()
            for d in data:
                NameServerRecord.objects.get_or_create(zone=self.zone, data=d)


class CnameRecipe(Recipe):
    """ Superclass for CNAME Recipe """

    data = None

    def __init__(self, zone):
        super(CnameRecipe, self).__init__(zone)
        self.set_cname(self.data)

    def set_cname(self, data):
        if data is not None:
            for d, t, ttl in data:
                CanonicalNameRecord.objects.get_or_create(zone=self.zone, data=d, target=t, ttl=ttl)


class MxRecipe(Recipe):
    """ Superclass for MX Recipe """

    data = None

    def __init__(self, zone):
        super(MxRecipe, self).__init__(zone)
        self.set_mx(self.data)

    def set_mx(self, data):
        if data is not None:
            # Remove existing MX
            MailExchangeRecord.objects.filter(zone=self.zone).delete()
            for p, d, ttl in data:
                MailExchangeRecord.objects.get_or_create(zone=self.zone, data=d, priority=p, ttl=ttl)


class SPFRecipe(Recipe):
    """ Superclass for Text Recipe """

    data = None

    def __init__(self, zone):
        super(SPFRecipe, self).__init__(zone)
        self.set_spf(self.data)

    def set_spf(self, data):
        if data is not None:
            # Remove existing SPF
            TextRecord.objects.filter(zone=self.zone, text__startswith='"v=spf1').delete()
            for spf, ttl in data:
                TextRecord.objects.get_or_create(zone=self.zone, text=spf, ttl=ttl)


class ServiceRecipe(Recipe):
    """ Superclass for Service Recipe """

    data = None

    def __init__(self, zone):
        super(ServiceRecipe, self).__init__(zone)
        self.set_service(self.data)

    def set_service(self, data):
        if data is not None:
            for data, target, priority, weight, port,  ttl in data:
                ServiceRecord.objects.get_or_create(zone=self.zone, priority=priority, weight=weight, port=port, target=target, data=data, ttl=ttl)


class Office365(CnameRecipe, MxRecipe, SPFRecipe, ServiceRecipe):

    data_mx = [
        ('0', 'healthbanc-com.mail.protection.outlook.com.', 3600),
    ]

    data_cname = [
        ('autodiscover', 'autodiscover.outlook.com.', 3600),
        ('lyncdiscover', 'webdir.online.lync.com.', 3600),
        ('sip', 'sipdir.online.lync.com.', 3600),
        ('msoid', 'clientconfig.microsoftonline-p.net.', 3600),
    ]

    data_spf = [
        ('"v=spf1 include:spf.protection.outlook.com -all"', 3600),
    ]

    # data, target, priority, weight, port,  ttl
    data_service = [
        ('_sipfederationtls._tcp', 'sipfed.online.lync.com.', 100, 1, 5061, 3600),
        ('_sip._tls', 'sipdir.online.lync.com.', 100, 1, 443, 3600),
    ]

    def __init__(self, zone):
        super(Office365, self).__init__(zone)
        self.set_mx(self.data_mx)
        self.set_cname(self.data_cname)
        self.set_spf(self.data_spf)
        self.set_service(self.data_service)


class GoogleApps(CnameRecipe, MxRecipe):

    data_cname = [
        ('calendar', 'ghs.googlehosted.com.', None),
        ('docs', 'ghs.googlehosted.com.', None),
        ('mail', 'ghs.googlehosted.com.', None),
        ('sites', 'ghs.googlehosted.com.', None),
        ('video', 'ghs.googlehosted.com.', None),
    ]

    data_mx = [
        ('10', 'aspmx.l.google.com.', None),
        ('20', 'alt1.aspmx.l.google.com.', None),
        ('20', 'alt2.aspmx.l.google.com.', None),
        ('30', 'alt3.aspmx.l.google.com.', None),
        ('30', 'alt4.aspmx.l.google.com.', None),
    ]

    def __init__(self, zone):
        super(GoogleApps, self).__init__(zone)
        self.set_cname(self.data_cname)
        self.set_mx(self.data_mx)


class RemovePerRecordTtls(Recipe):
    """ Remove Per Record TTLs """
    def __init__(self, zone):
        super(RemovePerRecordTtls, self).__init__(zone)
        AddressRecord.objects.filter(zone=self.zone).update(ttl=None)
        CanonicalNameRecord.objects.filter(zone=self.zone).update(ttl=None)
        MailExchangeRecord.objects.filter(zone=self.zone).update(ttl=None)
        NameServerRecord.objects.filter(zone=self.zone).update(ttl=None)
        TextRecord.objects.filter(zone=self.zone).update(ttl=None)
        ServiceRecord.objects.filter(zone=self.zone).update(ttl=None)


class ResetZoneDefaults(Recipe):
    """ Reset Zone TTLs, expiry etc """
    def __init__(self, zone):
        super(ResetZoneDefaults, self).__init__(zone)
        self.zone.refresh = ZONE_DEFAULTS['refresh']
        self.zone.retry = ZONE_DEFAULTS['retry']
        self.zone.expire = ZONE_DEFAULTS['expire']
        self.zone.minimum = ZONE_DEFAULTS['minimum']
        self.zone.ttl = ZONE_DEFAULTS['ttl']
        self.zone.soa_email = ZONE_DEFAULTS['soa']


class ReSave(Recipe):
    """ Force resave of the zone """
    pass  # Null recipe


class ReValidate(Recipe):
    """ Force revalidation of the zone """
    def __init__(self, zone):
        super(ReValidate, self).__init__(zone)
        self.zone.clear_cache()

    def save(self):
        pass
