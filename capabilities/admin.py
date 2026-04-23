from django.contrib import admin

from capabilities.models import (
    CapabilityItem,
    CapabilityState,
    Cluster,
    Outlet,
    SharedTag,
)


class CapabilityItemInline(admin.TabularInline):
    model = CapabilityItem
    extra = 0
    fields = ("order", "name", "priority", "baseline", "template_able", "phase", "assessment_method")
    ordering = ("order", "name")


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "desk", "item_count")
    list_display_links = ("name",)
    list_filter = ("desk",)
    ordering = ("desk", "order")
    search_fields = ("name", "description")
    inlines = [CapabilityItemInline]

    def item_count(self, obj):
        return obj.items.count()


@admin.register(CapabilityItem)
class CapabilityItemAdmin(admin.ModelAdmin):
    list_display = ("cluster", "name", "priority", "baseline", "template_able", "phase", "assessment_method")
    list_filter = ("cluster__desk", "cluster", "priority", "baseline", "phase", "assessment_method")
    search_fields = ("name", "description", "cross_desk_dep")
    ordering = ("cluster__order", "cluster__name", "order", "name")


@admin.register(SharedTag)
class SharedTagAdmin(admin.ModelAdmin):
    list_display = ("dimension", "value")
    list_filter = ("dimension",)
    search_fields = ("value",)


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ("name", "cohort", "enrolment_date", "data_champion")
    list_filter = ("cohort",)
    search_fields = ("name", "slug", "notes")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("tags",)


@admin.register(CapabilityState)
class CapabilityStateAdmin(admin.ModelAdmin):
    list_display = ("set_at", "outlet", "item", "level", "led_by_champion", "set_by", "llm_proposed")
    list_filter = ("level", "led_by_champion", "llm_proposed", "item__cluster")
    search_fields = ("outlet__name", "item__name", "evidence_excerpt")
    readonly_fields = ("set_at",)
    date_hierarchy = "set_at"
