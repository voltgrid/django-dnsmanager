from django.contrib import admin
import reversion

import settings
from signals import zone_fully_saved_signal


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


@admin.register(Zone)
class ZoneAdmin(reversion.VersionAdmin):
    inlines = [AddressRecordInline,
               CanonicalNameRecordInline,
               MailExchangeRecordInline,
               NameServerRecordInline,
               TextRecordInline,
               ServiceRecordInline]
    list_display = ('__unicode__', 'is_valid', 'is_delegated')
    list_filter = settings.DNS_MANAGER_ZONE_ADMIN_FILTER

    def run_recipe(self, recipe):
        """ Execute the given recipe from the recipe model """
        @reversion.create_revision()
        def apply_recipe(modeladmin, request, queryset):
            for zone in queryset.all():
                recipe(zone)
                zone.save()
                zone_fully_saved_signal.send(sender=self.__class__, instance=zone, created=False)
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

    def response_add(self, request, obj, post_url_continue=None):
        obj = self.after_saving_model_and_related_inlines(obj, created=True)
        return super(ZoneAdmin, self).response_add(request, obj)

    def response_change(self, request, obj):
        obj = self.after_saving_model_and_related_inlines(obj, created=False)
        return super(ZoneAdmin, self).response_change(request, obj)

    def after_saving_model_and_related_inlines(self, obj, created):
        zone_fully_saved_signal.send(sender=self.__class__, instance=obj, created=created)
        return obj