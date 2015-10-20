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
            for d, t in data:
                CanonicalNameRecord.objects.get_or_create(zone=self.zone, data=d, target=t)


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
            for p, d in data:
                MailExchangeRecord.objects.get_or_create(zone=self.zone, data=d, priority=p)


class GoogleApps(CnameRecipe, MxRecipe):

    data_cname = [
        ('calendar', 'ghs.googlehosted.com.'),
        ('docs', 'ghs.googlehosted.com.'),
        ('mail', 'ghs.googlehosted.com.'),
        ('sites', 'ghs.googlehosted.com.'),
        ('video', 'ghs.googlehosted.com.'),
    ]

    data_mx = [
        ('10', 'aspmx.l.google.com.'),
        ('20', 'alt1.aspmx.l.google.com.'),
        ('20', 'alt2.aspmx.l.google.com.'),
        ('30', 'alt3.aspmx.l.google.com.'),
        ('30', 'alt4.aspmx.l.google.com.'),
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
