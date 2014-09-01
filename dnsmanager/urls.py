from django.contrib.auth.decorators import permission_required
from django.conf.urls import patterns, url

from .views import ZoneListView, ZoneDetailView

urlpatterns = patterns('',
    url(r'^zone/$',
        permission_required('zone.view_zones')(ZoneListView.as_view()),
        name='zone_list'),
    url(r'^zone/(?P<pk>[\-\d\w]+)$',
        permission_required('zone.view_zones')(ZoneDetailView.as_view()),
        name='zone_detail'),
)