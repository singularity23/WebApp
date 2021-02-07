import datetime
import os

import bleach
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.models import Group, User

from todo.defaults import defaults
from todo.features import HAS_TASK_MERGE
from todo.forms import HazardForm
from todo.models import Attachment, Comment, Hazard, RiskLevel, Project
from todo.utils import (
    send_email_to_thread_participants,
    staff_check,
    user_can_read_hazard,
)

if HAS_TASK_MERGE:
    from dal import autocomplete


def handle_add_comment(request, task):
    if not request.POST.get("add_comment"):
        return

    Comment.objects.create(
        author=request.user, task=task, body=bleach.clean(request.POST["comment-body"], strip=True)
    )

    send_email_to_thread_participants(
        task,
        request.POST["coent-body"],
        request.user,
        subject='New comment posted on task "{}"'.format(task.title),
    )

    messages.success(request, "Comment posted. Notification email sent to thread participants.")


@login_required
@user_passes_test(staff_check)
def hazard_details(request, project_id, project_slug, hazard_id: int) -> HttpResponse:
    """View task details. Allow task details to be edited. Process new comments on task.
    """
    form1 = None
    hazard = get_object_or_404(Hazard, pk=hazard_id)
    project= get_object_or_404(Project, pk=project_id)
    comment_list = Comment.objects.filter(hazard=hazard).order_by("-date")

    # Ensure user has permission to view task. Superusers can view all tasks.
    # Get the group this task belongs to, and check whether current user is a member of that group.
    if not user_can_read_hazard(hazard, request.user):
        raise PermissionDenied

    # Save submitted comments
    handle_add_comment(request, hazard)
    print(hazard.project)
    # Save task edits
    if not request.POST.get("add_edit_hazard"):
        form1 = HazardForm(request.user, instance=hazard)
    else:
        form1 = HazardForm(
            request.user, request.POST, instance=hazard
        )

        if form1.is_valid():
            print("saved")

            item = form1.save(commit=False)

            #item.note = bleach.clean(form.cleaned_data["note"], strip=True)
            #item.title = bleach.clean(form.cleaned_data["title"], strip=True)
            item.project = project
            item.res_risk_level = RiskLevel.objects.filter(id=hazard.res_idex)[0]

            item.save()
            #print(form1)
            messages.success(request, "The hazard has been edited.")
            return redirect(
                "todo:project_details", project_id, project_slug
            )

    # Mark complete
    #if request.POST.get("toggle_done"):
    #    results_changed = toggle_task_completed(task.id)
    #    if results_changed:
    #        messages.success(request, f"Changed completion status for task {task.id}")

    #    return redirect("todo:task_detail", task_id=task.id)

    #if task.due_date:
    #    thedate = task.due_date
    #else:
    #    thedate = datetime.datetime.now()

    ## Handle uploaded files
    #if request.FILES.get("attachment_file_input"):
    #    file = request.FILES.get("attachment_file_input")

    #    if file.size > defaults("TODO_MAXIMUM_ATTACHMENT_SIZE"):
    #        messages.error(request, f"Fiale exceeds maximum attachment size.")
    #        return redirect("todo:task_detail", task_id=task.id)

    #    name, extension = os.path.splitext(file.name)

    #    if extension not in defaults("TODO_LIMIT_FILE_ATTACHMENTS"):
    #        messages.error(request, f"This site does not allow upload of {extension} files.")
    #        return redirect("todo:task_detail", task_id=task.id)

    #    Attachment.objects.create(
    #        task=task, added_by=request.user, timestamp=datetime.datetime.now(), file=file
    #    )
    #    messages.success(request, f"File attached successfully")
    #    return redirect("todo:task_detail", task_id=task.id)

    context = {
        "hazard": hazard,
        #"comment_list": comment_list,
        "form1": form1,
        #"merge_form": merge_form,
        #"thedate": thedate,
        #"comment_classes": defaults("TODO_COMMENT_CLASSES"),
        #"attachments_enabled": defaults("TODO_ALLOW_FILE_ATTACHMENTS"),
    }

    return render(request, "todo/hazard_details.html", context)
