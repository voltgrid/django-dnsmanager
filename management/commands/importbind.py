import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models.loading import get_model
from dnsmanager.models import Zone


class Command(BaseCommand):
    args = '<zone_file zone_file ...>'
    help = 'Import the specified Bind zone file'

    def handle(self, *args, **options):

        if int(options.get("verbosity", 1)) > 1:
            verbose = True
        else:
            verbose = False

        for zone_file in args:
            # assume filename is domain
            domain = os.path.splitext(os.path.basename(zone_file))[0]

            # Dynamically load our Domain name providing model
            app_label, model_name = settings.DNS_MANAGER_DOMAIN_MODEL.rsplit('.', 1)
            domain_model = get_model(app_label, model_name)
            domain_obj = domain_model.objects.get(name=domain)

            # Domain must already be created in accounts
            zone, created = Zone.objects.get_or_create(domain=domain_obj)

            with open(zone_file, mode='r') as f:
                text = f.read()

            zone.update_from_text(text)

            self.stdout.write('Successfully imported file "%s"' % zone_file)