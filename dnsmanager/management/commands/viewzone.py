from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from dnsmanager.models import Zone


class Command(BaseCommand):
    args = '<zone_id | none>'
    help = 'View a the specified Bind zone or bind zone list'

    def handle(self, *args, **options):

        if len(args) == 0:
            zone_list = Zone.objects.all()
            rendered = render_to_string('dnsmanager/zone_list.txt', {'object_list': zone_list})
            self.stdout.write('%s' % rendered)
        else:
            for zone_id in args:
                zone = Zone.objects.get(pk=zone_id)
                self.stdout.write('%s' % zone.render())