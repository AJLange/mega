"""
This reroutes from an URL to a python view-function/class.

The main web/urls.py includes these routes for all urls (the root of the url)
so it can reroute to all website pages.

"""

from django.urls import path
from .views import index

from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns

# add patterns here
from web.website.views import (index, policy, logs, setting, timeline, sitemap, cutscenes, characters)

urlpatterns = [
    path("", index.EvenniaIndexView.as_view(), name="index"),
    path("characters/", characters.CharacterListView.as_view(), name="characters"),
    path("policies/", policy.PolicyView.as_view(), name="policies"),
    path("setting/", setting.SettingView.as_view(), name="setting"),
    path("timeline/", timeline.TimelineView.as_view(), name="timeline"),
    path("logs/", logs.LogsIndexView.as_view(), name="logs"),
    path("cutscenes/", cutscenes.CutsceneIndexView.as_view(), name="cutscenes"),
    path("sitemap/", sitemap.SitemapView.as_view(), name="sitemap")

]

# read by Django
urlpatterns = urlpatterns + evennia_website_urlpatterns



