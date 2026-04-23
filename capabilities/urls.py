from django.urls import path

from capabilities import views

app_name = "capabilities"

urlpatterns = [
    path("", views.outlet_list, name="outlet_list"),
    path("taxonomy/", views.taxonomy_browser, name="taxonomy_browser"),
    path("outlet/<slug:slug>/", views.outlet_detail, name="outlet_detail"),
    path("outlet/<slug:slug>/state/new/", views.capability_state_create, name="state_create"),
    path("outlet/<slug:slug>/why-stuck/", views.why_stuck, name="why_stuck"),
    path("outlet/<slug:slug>/mismatch/run/", views.mismatch_run, name="mismatch_run"),
]
