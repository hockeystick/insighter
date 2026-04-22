from django.contrib import admin

from diagnostics.models import (
    CheckIn,
    Deployment,
    Diagnostic,
    Specialist,
    Sponsor,
)


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ("date", "outlet", "conducted_by", "status")
    list_filter = ("status", "date")
    search_fields = ("outlet__name", "notes_raw", "notes_summary")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "availability_hours_per_week")
    search_fields = ("display_name", "user__username")
    filter_horizontal = ("tags",)


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ("specialist", "outlet", "start_date", "end_date", "hours_committed")
    list_filter = ("start_date",)
    search_fields = ("specialist__display_name", "outlet__name", "handover_notes")


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("outlet", "milestone_day", "scheduled_for", "responded_at")
    list_filter = ("milestone_day",)
    search_fields = ("outlet__name",)


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "funding_notes")
    filter_horizontal = ("tags",)
