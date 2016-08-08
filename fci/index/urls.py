# coding: utf-8
from rest_framework.routers import DefaultRouter

from fci.index import views


router = DefaultRouter(trailing_slash=False)
router.register('resources', views.ResourceView)


urlpatterns = router.urls
