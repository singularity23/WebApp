import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from todo.models import Attachment
from todo.utils import remove_attachment_file


@login_required
def remove_attachment(request, project_id, project_slug, hazard_id, attachment_id: int):

    """Delete a previously posted attachment object and its corresponding file
    from the filesystem, permissions allowing.
    """

    if request.method == "POST":
        attachment = get_object_or_404(Attachment, id=attachment_id)

        # Permissions
        if not (
            attachment.hazard.project.group in request.user.groups.all()
            or request.user.is_superuser
        ):
            raise PermissionDenied

        if remove_attachment_file(attachment.pk):
            messages.success(request, f"Attachment {attachment.pk} removed.")
            #os.remove(attachment.file.url)
        else:
            messages.error(
                request, f"Sorry, there was a problem deleting attachment {attachment.pk}."
            )

        return redirect("todo:hazard_details", project_id, project_slug, hazard_id)

    else:
        raise PermissionDenied
