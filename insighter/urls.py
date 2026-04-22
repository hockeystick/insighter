from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('capabilities.urls')),
    path('diagnostics/', include('diagnostics.urls')),
]
