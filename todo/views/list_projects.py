import datetime

import bleach
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.text import slugify
from django.db import IntegrityError
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, User

from todo.forms import SearchForm, ProjectForm
from todo.models import Project, Hazard
from todo.utils import staff_check


@login_required
@user_passes_test(staff_check)
def list_projects(request) -> HttpResponse:
    """Homepage view - list of lists a user can view, and ability to add a list.
    """
    form = None
    thedate = datetime.datetime.now()
    searchform = SearchForm(auto_id=False)

    # Make sure user belongs to at least one group.
    if not request.user.groups.all().exists():
        messages.warning(
            request,
            "You do not yet belong to any groups. Ask your administrator to add you to one.",
        )
    projects = None
    # Superusers see all lists
    if request.user.is_superuser:
        projects = Project.objects.all().order_by("POR", "number")
    else:
        projects = Project.objects.filter(POR=request.user).order_by(
            "POR", "number"
        )
    
    
    project_count = projects.count()

    ####Add Project###

    if request.POST.getlist("add_edit_project"):
        form = ProjectForm(request.user, request.POST, initial = {"POR": request.user.id,                                                                  
                                                                  })
        if form.is_valid():
            print ("valid")
            try:
                newlist = form.save(commit=False)
                newlist.slug = slugify(newlist.number, allow_unicode=True)
                newlist.project_scope = bleach.clean(form.cleaned_data["project_scope"], strip=True)
                newlist.save()
                form.save()
                messages.success(request, "A new list has been added.")
                return redirect("todo:projects")

            except IntegrityError:
                messages.warning(
                    request,
                    "There was a problem saving the new list. "
                    "Most likely a list with the same name in the same group already exists.",
                )
    else:

        if request.user.groups.all().count() == 1:
            # FIXME: Assuming first of user's groups here; better to prompt for group
            form = ProjectForm(request.user, initial = {"POR": request.user.id})
        else:
            form = ProjectForm(request.user)

    context = {
        "projects": projects,
        "thedate": thedate,
        "searchform": searchform,
        "project_count": project_count,
        "form": form,
     
    }

    return render(request, "todo/list_projects.html", context)
