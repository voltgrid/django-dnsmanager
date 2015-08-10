
from .models import AddressRecord
from .models import CanonicalNameRecord
from .models import MailExchangeRecord
from .models import NameServerRecord
from .models import TextRecord
from .models import ServiceRecord
from .settings import ZONE_DEFAULTS
from .signals import zone_fully_saved_signal


class Recipe(object):
    """ Custom Zone Recipe """

    def __init__(self, zone):
        self.zone = zone


class GoogleApps(Recipe):

    def __init__(self, zone):
        super(GoogleApps, self).__init__(zone)
        self.set_cname()
        self.set_mx()

    def set_cname(self):

        data = [
            ('calendar', 'ghs.googlehosted.com.'),
            ('docs', 'ghs.googlehosted.com.'),
            ('mail', 'ghs.googlehosted.com.'),
            ('sites', 'ghs.googlehosted.com.'),
            ('video', 'ghs.googlehosted.com.'),
        ]

        for d, t in data:
            CanonicalNameRecord.objects.get_or_create(zone=self.zone, data=d, target=t)

    def set_mx(self):

        data = [
            ('10', 'aspmx.l.google.com.'),
            ('20', 'alt1.aspmx.l.google.com.'),
            ('20', 'alt2.aspmx.l.google.com.'),
            ('30', 'alt3.aspmx.l.google.com.'),
            ('30', 'alt4.aspmx.l.google.com.'),
        ]

        # Remove existing MX
        MailExchangeRecord.objects.filter(zone=self.zone).delete()

        for p, d in data:
            MailExchangeRecord.objects.get_or_create(zone=self.zone, data=d, priority=p)


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
    def __init__(self, zone):
        super(ReSave, self).__init__(zone)
        zone_fully_saved_signal.send(sender=self.__class__, instance=self.zone, created=False)


class NameServerRecipe(Recipe):
    """ Superclass for Name Server Recipe """
    data = None

    def __init__(self, zone):
        super(NameServerRecipe, self).__init__(zone)
        self.set_ns()

    def set_ns(self):

        # Remove existing NS
        NameServerRecord.objects.filter(zone=self.zone).delete()

        for d in self.data:
            NameServerRecord.objects.get_or_create(zone=self.zone, data=d)


class MxRecipe(Recipe):

    data = None

    def __init__(self, zone):
        super(MxRecipe, self).__init__(zone)
        self.set_mx()

    def set_mx(self):

        # Remove existing MX
        MailExchangeRecord.objects.filter(zone=self.zone).delete()

        for p, d in self.data:
            MailExchangeRecord.objects.get_or_create(zone=self.zone, data=d, priority=p)