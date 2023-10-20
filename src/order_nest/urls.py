from django.contrib import admin
from django.urls import path, include
from django_select2 import urls as django_select2_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path("select2/", include("django_select2.urls")),
    path('', include('webapp.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
]
