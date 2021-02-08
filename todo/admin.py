import csv
import datetime

from django.contrib import admin
from django.http import HttpResponse

from todo.models import Attachment, Comment, Hazard, Project, RiskLevel, ControlMeasure, Person, Engagement, Region, Location, Stage

def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f"attachment; filename={opts.verbose_name}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = content_disposition
    writer = csv.writer(response)
    fields = [
        field for field in opts.get_fields() if not (field.many_to_many and not field.one_to_many)
    ]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            data_row.append(value)
        writer.writerow(data_row)
    return response

export_to_csv.short_description = "Export to CSV"

class ProjectAdmin(admin.ModelAdmin):
    list_display = ("number", "group", "POR")
    #list_filter = ("task_list",)
    ordering = ("number",)
    search_fields = ("number",)
    actions = [export_to_csv]

class HazardAdmin(admin.ModelAdmin):
    list_display = ("description", "risk_level", "control_measure", "note", "assigned_to", "res_risk_level", "project")
    #list_filter = ("task_list",)
    ordering = ("risk_level",)
    search_fields = ("description",)
    actions = [export_to_csv]


class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "date", "snippet")


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("hazard", "added_by", "timestamp", "file")
    autocomplete_fields = ["added_by", "hazard"]

class RiskLevelAdmin(admin.ModelAdmin):
    list_display = ("level", "id")

class ControlMeasureAdmin(admin.ModelAdmin):
    list_display = ("measure","id")

class PersonAdmin(admin.ModelAdmin):
    list_display = ("project","first_name", "last_name","Email","is_team_member", "is_stakeholder", "role")

class EngagementAdmin(admin.ModelAdmin):
    list_display = ("project", "date", "body")

class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)

class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "region")

class StageAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)


admin.site.register(Project, ProjectAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Hazard, HazardAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(RiskLevel, RiskLevelAdmin)
admin.site.register(ControlMeasure, ControlMeasureAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Engagement, EngagementAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Stage, StageAdmin)
