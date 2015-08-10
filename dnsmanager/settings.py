from django.conf import settings

ZONE_DEFAULTS = dict()
ZONE_DEFAULTS['refresh'] = 28800    # 8 hours
ZONE_DEFAULTS['retry'] = 7200       # 2 hours
ZONE_DEFAULTS['expire'] = 604800    # 1 week
ZONE_DEFAULTS['minimum'] = 600      # 10 minutes
ZONE_DEFAULTS['ttl'] = 3600         # 1 hour
ZONE_DEFAULTS['soa'] = 'dns-admin'

DNS_MANAGER_RECIPES_DEFAULT = (
            ('dnsmanager.recipes.GoogleApps', 'Set Google Apps MX / CNAME'),
            ('dnsmanager.recipes.RemovePerRecordTtls', 'Reset Record TTLs'),
            ('dnsmanager.recipes.ResetZoneDefaults', 'Reset Zone Defaults'),
            ('dnsmanager.recipes.ReSave', 'Force Resave / Publish')
        )

DNS_MANAGER_DOMAIN_MODEL = getattr(settings, 'DNS_MANAGER_DOMAIN_MODEL', None)
DNS_MANAGER_ZONE_ADMIN_FILTER = getattr(settings, 'DNS_MANAGER_ZONE_ADMIN_FILTER', None)
DNS_MANAGER_RECIPES = getattr(settings, 'DNS_MANAGER_RECIPES', DNS_MANAGER_RECIPES_DEFAULT)