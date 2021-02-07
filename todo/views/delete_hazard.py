from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from todo.models import Hazard
from todo.utils import staff_check


@login_required
@user_passes_test(staff_check)
def delete_hazard(request, project_id, project_slug, hazard_id: int) -> HttpResponse:
    """Delete specified task.
    Redirect to the list from which the task came.
    """

    if request.method == "POST":
        hazard = get_object_or_404(Hazard, pk=hazard_id)

        redir_url = reverse(
            "todo:hazard_list",
            kwargs={"project_id": project_id,
                    "project_slug": project_slug,
                    }
        )

        # Permissions
        if not ( (request.user.is_superuser)
                or (hazard.assigned_to == request.user)
                or (hazard.project.group in request.user.groups.all())
        ):
            raise PermissionDenied

        hazard.delete()

        messages.success(request, "Task '{}' has been deleted".format(hazard.description))
        return redirect(redir_url)

    else:
        raise PermissionDenied