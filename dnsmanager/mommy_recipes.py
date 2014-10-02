from django.conf import settings

from model_mommy.recipe import Recipe, foreign_key, seq
from model_mommy import mommy

from .models import Zone, AddressRecord, CanonicalNameRecord, MailExchangeRecord, \
    NameServerRecord, TextRecord, ServiceRecord

# Dynamically import the mommy_recipe for the DOMAIN_MODEL
# If `DNS_MANAGER_DOMAIN_MODEL = 'vg.accounts.Domains'` then
# this is equivalent to: `from vg.account.mommy_recipes import domain`

t = settings.DNS_MANAGER_DOMAIN_MODEL.rsplit('.', 1)[0]
module = __import__(t + '.mommy_recipes', fromlist=['domain'])
domain = getattr(module, 'domain')

zone = Recipe(Zone, domain=foreign_key(domain))

address_record = Recipe(AddressRecord, zone=foreign_key(zone), ip=mommy.generators.gen_ipv4(),)

cname_record = Recipe(CanonicalNameRecord, zone=foreign_key(zone))

mx_record = Recipe(MailExchangeRecord, zone=foreign_key(zone))

ns_record = Recipe(NameServerRecord, zone=foreign_key(zone))

text_record = Recipe(TextRecord, zone=foreign_key(zone), text='"%s"' % seq("test"))

service_record = Recipe(ServiceRecord, zone=foreign_key(zone))
