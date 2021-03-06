
ZONE_DEFAULTS_DEFAULT = dict()
ZONE_DEFAULTS_DEFAULT['refresh'] = 28800    # 8 hours
ZONE_DEFAULTS_DEFAULT['retry'] = 7200       # 2 hours
ZONE_DEFAULTS_DEFAULT['expire'] = 2419200   # 1 month
ZONE_DEFAULTS_DEFAULT['minimum'] = 600      # 10 minutes
ZONE_DEFAULTS_DEFAULT['ttl'] = 3600         # 1 hour
ZONE_DEFAULTS_DEFAULT['soa'] = 'hostmaster'

DNS_MANAGER_RECIPES_DEFAULT = (
    ('dnsmanager.recipes.GoogleApps', 'Set Google Apps MX / CNAME'),
    ('dnsmanager.recipes.Office365', 'Set Office 365 MX / CNAME / SPF / SRV'),
    ('dnsmanager.recipes.RemovePerRecordTtls', 'Reset Record TTLs'),
    ('dnsmanager.recipes.ResetZoneDefaults', 'Reset Zone Defaults'),
    ('dnsmanager.recipes.ReSave', 'Force Resave / Publish'),
    ('dnsmanager.recipes.ReValidate', 'Force Revalidation')
)

DNS_MANAGER_NAMESERVERS_DEFAULT = ('ns1.example.com.', 'ns2.example.com.')