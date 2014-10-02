from django.contrib import admin
from django.conf import settings

import reversion

from models import AddressRecord, CanonicalNameRecord, MailExchangeRecord, \
    NameServerRecord, TextRecord, ServiceRecord, Zone


class AddressRecordInline(admin.TabularInline):
    model = AddressRecord
    extra = 0


class CanonicalNameRecordInline(admin.TabularInline):
    model = CanonicalNameRecord
    extra = 0


class MailExchangeRecordInline(admin.TabularInline):
    model = MailExchangeRecord
    extra = 0


class NameServerRecordInline(admin.TabularInline):
    model = NameServerRecord
    extra = 0


class TextRecordInline(admin.TabularInline):
    model = TextRecord
    extra = 0


class ServiceRecordInline(admin.TabularInline):
    model = ServiceRecord
    extra = 0

class ZoneAdmin(reversion.VersionAdmin):
    inlines = [AddressRecordInline,
               CanonicalNameRecordInline,
               MailExchangeRecordInline,
               NameServerRecordInline,
               TextRecordInline,
               ServiceRecordInline]
    list_display = ('__unicode__', 'is_valid')
    list_filter = ('domain__account', )

    def run_recipe(self, recipe):
        """ Execute the given recipe from the recipe model """
        @reversion.create_revision()
        def apply_recipe(modeladmin, request, queryset):
            for zone in queryset.all():
                recipe(zone)
                zone.save()
        return apply_recipe

    def get_actions(self, request):
        """ Set our custom recipe actions """
        actions = super(ZoneAdmin, self).get_actions(request)
        for item in settings.DNS_MANAGER_RECIPES:
            package, name = item[0].rsplit('.', 1)
            module = __import__(package, fromlist=[name])
            cls = getattr(module, name)
            actions[item[1]] = (self.run_recipe(cls), item[1], item[1])
        return actions

admin.site.register(Zone, ZoneAdmin)