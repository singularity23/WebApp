import datetime
import json
import logging
import os

import bleach
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from todo.defaults import defaults
from todo.utils import (get_history_change_reason)
from .forms import (EngagementForm, HazardForm, PersonForm, ProjectForm,
                    ProjectLinkForm)
from .models import (Attachment, Comment, Engagement, Hazard, Location, Person, Project, RiskLevel)
from .validators import validate_project_number, validate_sap_id
from todo.utils import EGBC_folder, SPOT_folder, SBD_folder, PPM_folder


log = logging.getLogger(__name__)


def handle_add_comment(request, hazard):
    if not request.POST.get("add_comment"):
        return

    Comment.objects.create(
        author=request.user,
        hazard=hazard,
        body=bleach.clean(request.POST["comment-body"], strip=True)
        )

    """ send_email_to_thread_participants(
        hazard,
        request.POST["comment-body"],
        request.user,
        subject='New comment posted on task "{}"'.format(hazard.title),
    )
 """
    messages.success(request, "Comment posted. Notification email sent to thread participants.")


def handle_upload_files(request, project, hazard):
    hazard_id = hazard.id
    project_id = project.id
    project_slug = project.slug
    # Handle uploaded files
    if request.FILES.get("attachment_file_input"):
        file = request.FILES.get("attachment_file_input")
        if file.size > defaults("TODO_MAXIMUM_ATTACHMENT_SIZE"):
            messages.error(request, f"File exceeds maximum attachment size.")
            return redirect("todo:hazard_details", project_id=project_id, project_slug=project_slug,
                            hazard_id=hazard_id)

        name, extension = os.path.splitext(file.name)
        name = name.lower()
        extension = extension.lower()
        # print(extension)

        if not Attachment.objects.filter(file=file).exists():
            if extension not in defaults("TODO_LIMIT_FILE_ATTACHMENTS"):
                messages.error(request, f"This site does not allow upload of {extension} files.")
                return redirect("todo:hazard_details", project_id, project_slug, hazard_id)

            attachment = Attachment.objects.create(
                hazard=hazard, added_by=request.user, timestamp=datetime.datetime.now(), file=file
                )
            attachment_id = attachment.id
            attachment.save_to_local(project, hazard)
            messages.success(request, f"File attached successfully")
            return redirect("todo:hazard_details", project_id, project_slug, hazard_id)
    else:
        print("nothing uploaded")


class ProjectUpdateView(MultipleObjectMixin, View):
    model = Project
    ordering = ["POR", "number"]

    template_name = "todo/project_list.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        #messages.success(request, "testing")
        if request.user.is_superuser:
            self.object_list = self.get_queryset()
        else:
            self.object_list = self.get_queryset().filter(POR=request.user)
        return super(ProjectUpdateView, self).dispatch(request, *args, **kwargs)

    def check_permissions(self, *args, **kwargs):
        if not self.request.user.groups.filter(name="Engineer").exists() or not self.request.user.is_authenticated:
            raise PermissionDenied
            return redirect("todo:login")

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        print(request.resolver_match.view_name)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        context = self.get_context_data()
        form2 = ProjectForm(request.user, request.POST, initial={"Group" : Group.objects.get(name="Engineer")})

        if self.object_list.filter(number=request.POST['number']).exists():
            print("project number exists")
            messages.error(request, "project number exists")

        if self.object_list.filter(SAP_id=request.POST['SAP_id']).exists():
            print("SAP number exists")
            messages.error(request, "SAP number exists")

        if not validate_project_number(request.POST['number']):
            print("project number invalid")
            messages.error(request, "Project number is invalid")

        if not validate_sap_id(request.POST['SAP_id']):
            print("SAP id invalid")
            messages.error(request, "SAP number is invalid")

        #print(request.POST)
        #print(form2)
        if form2.is_valid():
            item = form2.save(commit=False)
            item.save()
            context['form2'] = form2
            return redirect("todo:project_list")
        else:
            messages.error(request, "Invalid form submitted")
        return render(request, self.template_name, context)


def _import_hazard(obj, project):
    dctn = obj.get("fields")
    risk_level_id = dctn['risk_level']

    hazard = Hazard(
        index=obj.get("pk"),
        description=dctn['description'],
        risk_level=RiskLevel.objects.get(id=risk_level_id),
        control_measure=dctn['control_measure'],
        note=dctn['note'],
        details=dctn['details'],
        res_risk_level=dctn['res_risk_level'],
        project=project,
        assigned_to=dctn['assigned_to'], )

    hazard.save()


def handle(project):
    filename = os.path.join(settings.BASE_DIR, "hazard.json")

    with open(filename, 'r') as json_file:
        objects = json.loads(json_file.read())
    for obj in objects:
        _import_hazard(obj, project)


class ProjectDetailView(SingleObjectMixin, View):
    model = Project
    template_name = "todo/project_details.html"
    slug_field = "slug"
    slug_url_kwarg = "project_slug"
    pk_url_kwarg = "project_id"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Project.objects.all())
        print(self.object.counts)
        print(self.object.SPOT_link)

        method = self.request.POST.get('_method', '').lower()
        if method == 'delete':
            return self.delete(request, *args, **kwargs)

        return super(ProjectDetailView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # print("2")
        context = self.get_context_data()

        form4 = EngagementForm(request.user, initial={"project": self.object})
        #print("stakeholders"+ str(form4.fields))
        form3 = ProjectLinkForm(request.user, instance=self.object)
        links = form3.save(commit=False)
        links.EGBC_link = EGBC_folder(self.object)
        links.SPOT_link = SPOT_folder(self.object)
        links.PPM_link = PPM_folder(self.object)
        links.SBD_link = SBD_folder(self.object)
        links.save()


        print("link"+str(form3.fields))
        form2 = ProjectForm(request.user, instance=self.object)

        form1 = HazardForm(request.user, initial={"project": self.object})

        form = PersonForm(request.user, initial={"project": self.object})
        context_extra = {
            "form"        : form,
            "form1"       : form1,
            "form2"       : form2,
            "form3"       : form3,
            "form4"       : form4,
            }
        context.update(context_extra)

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        self.project_id = project.id
        self.project_slug = project.slug
        persons = Person.objects.filter(project=project)
        engagements = Engagement.objects.filter(project=project)

        context_extra = {
            "engagements" : engagements,
            "project_id"  : self.project_id,
            "project_slug": self.project_slug,
            "project"     : self.object,
            "hazards"     : self.get_queryset(),
            "persons"     : persons,
            }

        context.update(context_extra)

        return context

    def get_queryset(self):
        return self.object.hazard_set.all()

    def post(self, request, *args, **kwargs):

        context = self.get_context_data()

        # print(engagements)
        print(request.POST)
        if request.POST.get("edit_link", "").lower() == "submit":
            form3 = ProjectLinkForm(request.user, request.POST, instance=self.object)
            print(form3)
            if form3.is_bound and form3.is_valid():
                item = form3.save(commit=False)
                item.project = self.object
                item.save()
                context["form3"] = form3
                return redirect("todo:project_details", self.project_id, self.project_slug)

            else:
                print("form3 errors")

        elif request.POST.get("edit_project", "").lower() == "submit":
            form2 = ProjectForm(request.user, request.POST, instance=self.object)
            #print(form2)
            if form2.is_bound and form2.is_valid():
                item = form2.save(commit=False)
                item.group = Group.objects.get(name="Engineer")
                item.project = self.object
                item.save()
                context["form2"] = form2
                return redirect("todo:project_details", self.project_id, self.project_slug)

            else:
                print("form2 errors")

        elif request.POST.get("edit_hazard", "") == "submit":
            form1 = HazardForm(request.user, request.POST, initial={"project": self.object})
            if form1.is_bound and form1.is_valid():
                new_item = form1.save(commit=False)
                new_item.project = self.object
                new_item.note = bleach.clean(form1.cleaned_data["note"], strip=True)
                new_item.save()
                context["form1"] = form1
                return redirect("todo:project_details", self.project_id, self.project_slug)

            else:
                print("form1 errors")

        elif request.POST.get("action", "") == "edit_person":
            method = request.POST.get("_method", "").lower()
            person_id = request.POST.get("person_id")
            person = None
            form = None

            if person_id:
                person = get_object_or_404(Person, pk=person_id)
                context["person_id"] = person_id

                if method == 'delete':
                    print("deleted")
                    person.delete()
                else:
                    form = PersonForm(request.user, request.POST, instance=person)
            else:
                form = PersonForm(request.user, request.POST)

            if form.is_bound and form.is_valid():
                item = form.save(commit=False)
                item.project = self.object
                item.save()

            else:
                print("form errors")

            context["form"] = form

            return redirect("todo:project_details", self.object.id, self.object.slug)

        elif request.POST.get("edit_engagement", "").lower() == "submit":
            form4 = EngagementForm(request.user, request.POST, initial={"project": self.object})
            if form4.is_valid():
                stakeholder_queryset = form4.cleaned_data["stakeholders"]
                stakeholder_list = list(stakeholder_queryset)
                #print(stakeholder_list)
                stakeholder_text = []
                for s in stakeholder_list:
                    stakeholder_text.append(str(s))

                #print(stakeholder_text)
                item = form4.save(commit=False)
                item.stakeholders_string = ', '.join(stakeholder_text)
                item.project = self.object
                item.date = datetime.datetime.now()
                # print(item.date)
                item.save()
                context["form4"] = form4
                return redirect("todo:project_details", self.object.id, self.object.slug)

            else:
                print("form4 errors")

        elif request.POST.get("action", "") == "load_defaults":
            handle(self.object)
        else:
            print("errors")
        print(context)

        return render(request, self.template_name, context)

    def delete(self, request, *args, **kwargs):

        self.object.delete()
        messages.success(request, "#{project_number} is gone.".format(project_number=self.object.number))
        return redirect("todo:project_list")

def load_locations(request):
    region_id = request.GET.get('region_id')
    locations = Location.objects.filter(region_id=region_id).all()
    return render(request, 'todo/include/locations_dropdown_list.html', {'locations': locations})

class HazardDetailView(SingleObjectMixin, View):
    model = Hazard
    template_name = "todo/hazard_details.html"
    pk_url_kwarg = "hazard_id"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        method = self.request.POST.get('_method', '').lower()
        if method == 'delete':
            return self.delete(request, *args, **kwargs)

        self.object = self.get_object(queryset=Hazard.objects.all())
        self.hazard_id = self.kwargs.get("hazard_id")
        self.project_id = self.kwargs.get("project_id")
        self.project_slug = self.kwargs.get("project_slug")
        self.project = get_object_or_404(Project, id=self.project_id)
        self.comment_list = Comment.objects.filter(hazard=self.object).order_by("-date")
        self.attachments = Attachment.objects.filter(hazard=self.object)

        return super(HazardDetailView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # print("2")
        context = self.get_context_data()
        form1 = HazardForm(request.user, instance=self.object)
        context['records'] = get_history_change_reason(self.object)
        # context['old_record'] = old_record
        context['form1'] = form1

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # print("3")
        context = self.get_context_data()
        hazard = self.object
        hazard_id = self.object.id
        hazard_res_id = hazard.res_idex
        hazard_res_level = hazard.res_level
        print(hazard_res_id)
        print(hazard_res_level)
        print(request.POST)
        form1 = HazardForm(request.user, request.POST, instance=hazard)
        if request.POST.get("edit_hazard") == 'submit' and form1.is_valid():
            item = form1.save(commit=False)
            item.project = self.project
            item.res_risk_level = RiskLevel.objects.filter(pk=self.object.res_idex)[0]
            print(item.res_risk_level)
            item.save()
            # print(form1)
            messages.success(request, "The hazard has been edited.")
            return redirect(
                "todo:hazard_details", self.project_id, self.project_slug, hazard_id)
        elif request.POST.get("attachment_file_input") == "submit":
            handle_upload_files(request, self.project, hazard)
            return redirect(
                "todo:hazard_details", self.project_id, self.project_slug, hazard_id)
        elif request.POST.get("add_comment") == "submit":
            handle_add_comment(request, hazard)
            return redirect(
                "todo:hazard_details", self.project_id, self.project_slug, hazard_id)
        else:
            messages.warning(request, "Updates not posted due to errors")

        context['form1'] = form1

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['hazard'] = self.object
        context['hazard_id'] = self.hazard_id
        context['project'] = self.project
        context['project_id'] = self.project_id
        context['project_slug'] = self.project_slug
        context['attachments'] = self.attachments
        context['comment_list'] = self.comment_list
        context['comment_classes'] = defaults("TODO_COMMENT_CLASSES")
        context['attachments_enabled'] = defaults("TODO_ALLOW_FILE_ATTACHMENTS")
        return context


    def delete(self, request, *args, **kwargs):

        self.object.delete()
        messages.success(request, "Hazard #{obj} has been deleted.".format(obj=self.object.id))

        return redirect("todo:project_details", self.project_id, self.project_slug)


class HazardListView(ProjectDetailView):
    template_name = "todo/hazard_list.html"


class TeamListView(ProjectDetailView):

    template_name = "todo/team_list.html"



""" class DocumentListView(ListView, mypath=None):

    if mypath == None:
        mypath = r"D:/documents/LMN/Vancouver"

    for (urls, dirnames, filenames) in walk(mypath):

        for dir in dirnames:
            path = os.path.join(dirpath, dir)
            rel_dir = os.path.relpath(path, start=mypath)

        for file in filenames:
            filepath = os.path.join(dirpath, dir, file)
            f.append(filepath) """
