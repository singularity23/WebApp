from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from todo.models import Person
from todo.utils import staff_check


@login_required
@user_passes_test(staff_check)
def delete_person(request, project_id, project_slug, person_id: int) -> HttpResponse:
    """Delete specified task.
    Redirect to the list from which the task came.
    """

    if request.method == "POST":
        person = get_object_or_404(Person, pk=person_id)

        redir_url = reverse(
            "todo:team_list",
            kwargs={"project_id": project_id,
                    "project_slug": project_slug,
                    }
        )

        # Permissions
        if not (request.user.is_superuser):
            raise PermissionDenied

        person.delete()

        messages.success(request, "Task '{}' has been deleted".format(person.full_name))
        return redirect(redir_url)

    else:
        raise PermissionDenied
