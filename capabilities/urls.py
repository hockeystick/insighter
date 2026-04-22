from django.urls import path

from capabilities import views

app_name = "capabilities"

urlpatterns = [
    path("", views.outlet_list, name="outlet_list"),
    path("outlet/<slug:slug>/", views.outlet_detail, name="outlet_detail"),
    path("outlet/<slug:slug>/state/new/", views.capability_state_create, name="state_create"),
]
