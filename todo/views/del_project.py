from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from todo.models import Hazard, Project
from todo.utils import staff_check


@login_required
@user_passes_test(staff_check)
def del_project(request, project_id: int,) -> HttpResponse:
    """Delete an entire list. Only staff members should be allowed to access this view.
    """
    project = get_object_or_404(Project, pk=project_id)

    # Ensure user has permission to delete list. Get the group this list belongs to,
    # and check whether current user is a member of that group AND a staffer.
    if project.group not in request.user.groups.all():
        raise PermissionDenied    
    if not request.user.is_staff:
        raise PermissionDenied

    if request.method == "POST":
        Project.objects.get(id=project_id).delete()
        messages.success(request, "{project} is gone.".format(project=project.number))
        return redirect("todo:projects")
    else:
        project_done = Hazard.objects.filter(project=project_id, completed=True).count()
        project_undone = Hazard.objects.filter(project=project_id, completed=False).count()
        project_total = Hazard.objects.filter(project=project_id).count()

    context = {
        "project": project,
        "project_done": project_done,
        "project_undone": project_undone,
        "project_total": project_total,
    }

    return render(request, "todo/del_list.html", context)
