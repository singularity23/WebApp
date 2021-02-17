from django.urls import path

from todo import views, view
from .view import ProjectUpdateView, ProjectDetailView, HazardDetailView, HazardListView, TeamListView, load_locations
from django.conf.urls import url
from django.urls import include, path


from todo.features import HAS_TASK_MERGE

app_name = "todo"

urlpatterns = [
    path("", ProjectUpdateView.as_view(), name="project_list"),
    path("<int:project_id>/<str:project_slug>/", ProjectDetailView.as_view(), name="project_details"),
    path("<int:project_id>/<str:project_slug>/hazard/<int:hazard_id>/", HazardDetailView.as_view(), name="hazard_details"),
    path("<int:project_id>/<str:project_slug>/hazards/", HazardListView.as_view(), name="hazard_list"),

    path("<int:project_id>/<str:project_slug>/hazard/<int:hazard_id>/Delete", views.delete_hazard,
         name="hazard_delete"),

    path("<int:project_id>/<str:project_slug>/person/<int:person_id>/Delete", views.delete_person,
         name="person_delete"),
     path("<int:project_id>/<str:project_slug>/edit/<int:person_id>", views.team_list, name="team_edit"),

    path("<int:project_id>/<str:project_slug>/hazard/<int:hazard_id>/attachment/remove/<int:attachment_id>/",
         views.remove_attachment, name="remove_attachment"
    ),
    path("<int:project_id>/<str:project_slug>/team/", TeamListView.as_view(), name="team_list"),
    path('ajax/load-locations/', view.load_locations, name='ajax_load_locations'),# AJAX
]
