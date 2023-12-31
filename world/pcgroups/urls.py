from django.urls import path
from . import views
from evennia.web.website import views as website_views
from django.conf.urls import url

urlpatterns = [
    path('', views.groups, name='list'),
    url(
        r"^characters/detail/(?P<slug>[\w\d\-]+)/(?P<pk>[0-9]+)/$",
        website_views.GroupDetailView.as_view(),
        name="group-detail",
    )
]