from django.urls import path

from diagnostics import views

app_name = "diagnostics"

urlpatterns = [
    path("outlet/<slug:slug>/new/", views.diagnostic_create, name="diagnostic_create"),
    path("<int:pk>/", views.diagnostic_detail, name="diagnostic_detail"),
    path("<int:pk>/synthesis/run/", views.synthesis_run, name="synthesis_run"),
    path("<int:pk>/synthesis/review/", views.synthesis_review, name="synthesis_review"),
    path("<int:pk>/synthesis/accept/", views.synthesis_accept, name="synthesis_accept"),
]
