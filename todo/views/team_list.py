
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from todo.defaults import defaults
from todo.features import HAS_TASK_MERGE
from todo.forms import HazardForm, PersonForm, ProjectForm
from todo.models import Attachment, Comment, Hazard, Person, Project, RiskLevel
from todo.utils import (send_email_to_thread_participants, staff_check,
						user_can_read_hazard)

@login_required
@user_passes_test(staff_check)
def team_list(request, project_id=None, project_slug=None, person_id=None) -> HttpResponse:
	"""View task details. Allow task details to be edited. Process new comments on task.
	"""
	person=None
	if person_id:
		person = get_object_or_404(Person, pk=person_id)

	project = get_object_or_404(Project, pk=project_id)

	if request.method == 'POST':
		form = PersonForm(request.user, request.POST, instance=person)
		if form.is_valid():
			item=form.save(commit=False)
			item.project=project
			item.save()
			#print(form)
			return redirect("todo:project_details", project_id, project_slug)
	else:
		form = PersonForm(request.user, instance=person)

	#if request.POST.getlist("add_edit_person"):
	#	#print("new form2")
	#	form2 = PersonForm(request.user,
	#		request.POST,
	#		initial={"project": project})

	#	if form2.is_valid():
	#		new_person = form2.save(commit=False)
	#		new_person.project = project
	#		new_person.save()
	#		#print("saved")
	#		messages.success(request, 'New person "{t}" has been added.'.format(t=new_person.first_name))
	#		return redirect("todo:team_list", project_id, project_slug)
	#else:
	#	 form2 = PersonForm(request.user, initial={"project": project})



	#if not request.POST.get("add_edit_person"):

	#	form2 = PersonForm(request.user, instance=person)
	#	#print(person)

	#else:
	#	form2 = PersonForm(request.user, request.POST, instance=person)

	#	if form2.is_valid():
	#		new_person = form2.save(commit=False)
	#		new_person.project = project
	#		new_person.is_team_member = person.is_team_member
	#		new_person.is_stakeholder = person.is_stakeholder
	#		new_person.Email = person.Email
	#		new_person.role = person.role
	#		new_person.first_name = person.first_name
	#		new_person.last_name = person.last_name

	#		new_person.save()
	#		#print("saved")
	#		#print(form2)
	#		messages.success(request, 'New person "{t}" has been added.'.format(t=new_person.first_name))


	context = {
		"project": project,
		"person": person,
		"project_id": project_id,
		"project_slug": project_slug,
		"form":form,
		# "comment_classes": defaults("TODO_COMMENT_CLASSES"),
		# "attachments_enabled": defaults("TODO_ALLOW_FILE_ATTACHMENTS"),
	}
	return render(request, "todo/team_list.html", context)
