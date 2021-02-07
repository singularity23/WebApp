from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from todo.models import Hazard, Project
from todo.utils import staff_check


@login_required
@user_passes_test(staff_check)
def toggle_done(request, project_id: int) -> HttpResponse:
    """Toggle the completed status of a task from done to undone, or vice versa.
    Redirect to the list from which the task came.
    """

    if request.method == "POST":
        project = get_object_or_404(Project, pk=project_id)

        redir_url = reverse("todo:project_details", kwargs={"project_id": project_id,})

        # Permissions
        if not ( (request.user.is_superuser)
            or (project.POR == request.user)
            or (project.group in request.user.groups.all())
        ):
            raise PermissionDenied

       # toggle_task_completed(project_id)
        messages.success(request, "Task status changed for '{}'".format(project.number))

        return redirect(redir_url)

    else:
        raise PermissionDenied
