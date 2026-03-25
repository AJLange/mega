"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path
from .views import index

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns

# add patterns here
from web.website.views import index

urlpatterns = [
    path("", index.EvenniaIndexView.as_view(), name="index"),
    path("policies/", index.EvenniaIndexView.as_view(), name="policies"),
    path("setting/", index.EvenniaIndexView.as_view(), name="setting"),
    path("timeline/", index.EvenniaIndexView.as_view(), name="timeline")

]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns



