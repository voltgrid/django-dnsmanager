from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test import RequestFactory

from model_mommy import mommy

from .models import Zone, AddressRecord, CanonicalNameRecord, MailExchangeRecord, NameServerRecord, TextRecord

from .views import ZoneListView, ZoneDetailView


# Creation Tests
class DNSCreationTest(TestCase):

    def test_zone_creation(self):
        zone = mommy.make_recipe('dnsmanager.zone')
        self.assertTrue(isinstance(zone, Zone))
        return zone

    def test_address_record_creation(self):
        address_record = mommy.make_recipe('dnsmanager.address_record')
        self.assertTrue(isinstance(address_record, AddressRecord))
        return address_record

    def test_complex_zone_creation(self):
        zone = mommy.make_recipe('dnsmanager.zone')
        # records
        address_record_1 = mommy.make_recipe('dnsmanager.address_record', zone=zone, data='@')
        cname_record = mommy.make_recipe('dnsmanager.cname_record', zone=zone, data='www', target='@')
        mx_record = mommy.make_recipe('dnsmanager.mx_record', zone=zone, priority=10)
        ns_record_1 = mommy.make_recipe('dnsmanager.ns_record', zone=zone, data='ns1.example.com')
        ns_record_2 = mommy.make_recipe('dnsmanager.ns_record', zone=zone, data='ns2.example.com')
        text_record = mommy.make_recipe('dnsmanager.text_record', zone=zone, data="@", text='"v=spf1 a -all"')

        self.assertTrue(isinstance(zone, Zone))

    def test_zone_import(self):
        data = {"id": 63,
            "domain": "vaultgrid.com",
            "data": "$ORIGIN .\n$TTL 3600\nvaultgrid.com IN SOA ns1.cromova.net. dns-admin (\n 2013120600 ; serial\n 28800 ; refresh\n 7200 ; retry\n 604800 ; expire\n 600 ; nxdomain ttl (bind 9+)\n )\n\n$ORIGIN vaultgrid.com.\n\n; NameServerRecords\n\n@    3600    IN    NS    ns1.cromova.net.\n\n@    3600    IN    NS    ns2.cromova.net.\n\n\n; AddressRecords\n\n@    3600    IN    A    103.245.152.101\n\nwww    3600    IN    A    103.245.152.101\n\n\n; CanonicalNameRecord\n\n\n; MailExchangeRecord\n\n\n; TXT\n",
            "updated": "2013-12-06T04:30:12Z"
        }
        account = mommy.make_recipe('vg.account.account')
        domain, created = Domain.objects.get_or_create(name=data['domain'], account=account)
        zone, created = Zone.objects.get_or_create(domain=domain)
        zone.update_from_text(text=data['data'])

        self.assertEqual(zone.addressrecord_set.count(), 2)
        self.assertEqual(zone.nameserverrecord_set.count(), 2)
        self.assertNotEqual(zone.serial, 2013120600)


# Recipe Tests
from dnsmanager.recipes import GoogleApps, RemovePerRecordTtls, ResetZoneDefaults


class RecipeTest(TestCase):

    def test_create_zone(self):
        zone = mommy.make_recipe('dnsmanager.zone')
        # records
        address_record_1 = mommy.make_recipe('dnsmanager.address_record', zone=zone, data='@')
        cname_record = mommy.make_recipe('dnsmanager.cname_record', zone=zone, data='www', target='@')
        mx_record = mommy.make_recipe('dnsmanager.mx_record', zone=zone, priority=10)
        ns_record_1 = mommy.make_recipe('dnsmanager.ns_record', zone=zone, data='ns1.example.com')
        ns_record_2 = mommy.make_recipe('dnsmanager.ns_record', zone=zone, data='ns2.example.com')
        text_record = mommy.make_recipe('dnsmanager.text_record', zone=zone, data="@", text='"v=spf1 a -all"')
        return zone

    def test_google_apps_recipe(self):
        zone = mommy.make_recipe('dnsmanager.zone')
        # add a record that will be removed later
        mommy.make_recipe('dnsmanager.mx_record', zone=zone, priority=10)
        # run recipe
        GoogleApps(zone)
        self.assertEqual(zone.mailexchangerecord_set.all().count(), 5)
        self.assertGreaterEqual(zone.canonicalnamerecord_set.all().count(), 5)

    def test_remove_record_ttl_email(self):
        zone = mommy.make_recipe('dnsmanager.zone')
        # add a few records that will be used later
        mommy.make_recipe('dnsmanager.address_record', zone=zone, ttl='1111')
        mommy.make_recipe('dnsmanager.cname_record', zone=zone, ttl='2222')
        mommy.make_recipe('dnsmanager.mx_record', zone=zone, ttl='3333')
        mommy.make_recipe('dnsmanager.ns_record', zone=zone, ttl='4444')
        mommy.make_recipe('dnsmanager.text_record', zone=zone, ttl='5555')
        # run recipe
        RemovePerRecordTtls(zone)
        # check results
        for obj in zone.addressrecord_set.all():
            self.assertEqual(obj.ttl, None)
        for obj in zone.canonicalnamerecord_set.all():
            self.assertEqual(obj.ttl, None)
        for obj in zone.mailexchangerecord_set.all():
            self.assertEqual(obj.ttl, None)
        for obj in zone.nameserverrecord_set.all():
            self.assertEqual(obj.ttl, None)
        for obj in zone.textrecord_set.all():
            self.assertEqual(obj.ttl, None)

    def test_reset_zone_defaults(self):
        from .settings import ZONE_DEFAULTS
        from random import randint
        zone = mommy.make_recipe('dnsmanager.zone')
        # change our values
        zone.refresh = ZONE_DEFAULTS['refresh'] + randint(1, 10000)
        zone.retry = ZONE_DEFAULTS['retry'] + randint(1, 10000)
        zone.expire = ZONE_DEFAULTS['expire'] + randint(1, 10000)
        zone.minimum = ZONE_DEFAULTS['minimum'] + randint(1, 10000)
        zone.ttl = ZONE_DEFAULTS['ttl'] + randint(1, 10000)
        # run recipe
        ResetZoneDefaults(zone)
        # check results
        self.assertEqual(zone.refresh, ZONE_DEFAULTS['refresh'])
        self.assertEqual(zone.retry, ZONE_DEFAULTS['retry'])
        self.assertEqual(zone.expire, ZONE_DEFAULTS['expire'])
        self.assertEqual(zone.minimum, ZONE_DEFAULTS['minimum'])
        self.assertEqual(zone.ttl, ZONE_DEFAULTS['ttl'])


class ZoneTest(TestCase):

    def setUp(self):
        self.user = mommy.make_recipe('vg.account.user')
        # grant permission
        permission = Permission.objects.get(codename='view_zones')
        self.user.user_permissions.add(permission)
        self.account = mommy.make_recipe('vg.account.account', user=self.user)
        # Data
        self.domain_name = 'example.com.au'
        domain = mommy.make_recipe('vg.account.domain', name=self.domain_name)
        self.obj = mommy.make_recipe('dnsmanager.zone', domain=domain)
        self.factory = RequestFactory()

    def test_detail_view(self):
        # Actual request
        request = self.factory.get(reverse_lazy('zone_detail', kwargs={'pk': self.obj.domain.pk}))
        request.user = self.user
        view = ZoneDetailView.as_view()
        response = view(request, pk=self.obj.domain.pk)
        self.assertEqual(response.status_code, 200)

    def test_zone_list(self):
        request = self.factory.get(reverse_lazy('zone_list'))
        request.user = self.user
        view = ZoneListView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
