# coding: utf-8

from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # Fix for crash in rest framework.
    url(r'^fci/resources$', RedirectView.as_view(
        url='/fci/resources/', permanent=True)),
    url(r'^fci/', include('fci.index.urls'))
]
