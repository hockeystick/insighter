from django.urls import path

from diagnostics import views

app_name = "diagnostics"

urlpatterns = [
    path("outlet/<slug:slug>/new/", views.diagnostic_create, name="diagnostic_create"),
    path("<int:pk>/", views.diagnostic_detail, name="diagnostic_detail"),
]
