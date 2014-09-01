from django.views.generic import ListView
from django.views.generic import DetailView

from .models import Zone


class ZoneListView(ListView):
    model = Zone
    template_name = 'dnsmanager/zone_list.txt'

    def render_to_response(self, context, **response_kwargs):
        return super(ZoneListView, self).render_to_response(context, content_type='text/plain', **response_kwargs)


class ZoneDetailView(DetailView):
    queryset = Zone.objects.all()
    template_name = 'dnsmanager/zone_detail.txt'

    def render_to_response(self, context, **response_kwargs):
        return super(ZoneDetailView, self).render_to_response(context, content_type='text/plain', **response_kwargs)