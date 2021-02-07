
import bleach
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from todo.forms import HazardForm, PersonForm, ProjectForm
from todo.models import Hazard, Person, Project, RiskLevel
from todo.utils import send_notify_mail, staff_check


@login_required
@user_passes_test(staff_check)
def project_details(request, project_id=None, project_slug=None, person_id=None) -> HttpResponse:
	"""Display and manage tasks in a todo list.
	"""
	# Defaults
	form1 = None
	form2 = None
	hazards = None
	persons = None
	person = None
	address = ""

	project = get_object_or_404(Project, pk=project_id)
	if project.group in request.user.groups.all() or request.user.is_superuser:
		hazards = Hazard.objects.filter(project=project)
		persons = Person.objects.filter(project=project)

		# ######################
		#  Edit Project Form
		# ######################

		#project_a = Project(number=project.number, group=project.group)
		#print(project_a.group)

		#if not request.POST.get("add_edit_project"):
		#    print("Edit")

		if not request.POST.get("add_edit_project"):
			form2 = ProjectForm(request.user, instance = project)
			#print(form)
		else:
			form2 = ProjectForm(request.user, request.POST, instance = project)

			if form2.is_valid():
				print("here")
				item = form2.save(commit=False)
				item.slug = slugify(item.number, allow_unicode=True)
				item.project_scope = bleach.clean(form2.cleaned_data["project_scope"], strip=True)
				item.title = bleach.clean(form2.cleaned_data["title"], strip=True)
				item.save()
			else:
				print("errors : {}".format(form2.errors))

		#else:
		#    print("not edit")
		#    print(request.POST)
		#    project = Project(group=project.group)
		#    form = ProjectForm(request.user, request.POST,instance=project)
		#    print(form)

		#if form.is_valid():
		#    print("valid")
		#    item = form1.save(commit=False)
		#    item.slug = slugify(item.number, allow_unicode=True)
		#    item.project_scope = bleach.clean(form.cleaned_data["project_scope"],
		#    strip=True)
		#    #item.save()
		#    print(item)
		#    messages.success(request, "The list has been edited.")
		#    return redirect(
		#        "todo:project_details", project_id=project.id,
		#        project_slug=project.slug
		#    )

		# ######################
		#  Add Hazard
		# ######################

		if request.POST.getlist("add_edit_hazard"):
			#print(form1)
			form1 = HazardForm(request.user,
				request.POST,
				initial={"project": project},)

			if form1.is_valid():
				new_item = form1.save(commit=False)
				new_item.project = project
				new_item.note = bleach.clean(form1.cleaned_data["note"], strip=True)
				new_item.save()

				#print('saved')
				messages.success(request, 'New task "{t}" has been added.'.format(t=new_item.description))
				return redirect("todo:project_details", project_id=project.pk, project_slug=project.slug)
		else:
			# Don't allow adding new tasks on some views
			if project_slug not in ["mine", "recent-add", "recent-complete"]:
				form1 = HazardForm(request.user,
					initial={"project": project.pk},)

		# ######################
		#  Add Person
		# ######################
		#for person in persons:
		#	if person.id == person_id:
		#		print(person_id)
		#		if request.POST.getlist("add_edit_person"):
		#			print("new form2")
		#			form2 = PersonForm(request.user,
		#				request.POST,
		#				initial={"project": project})
		#			print(request.POST)
		#			if form2.is_valid():
		#				new_person = form2.save(commit=False)
		#				new_person.project = project
		#				new_person.save()
		#				print("saved")
		#				print(form2)
		#				messages.success(request, 'New person "{t}" has been added.'.format(t=new_person.first_name))
		#				return redirect("todo:project_details", project_id=project.id, project_slug=project.slug)
		#		else:
		#			 form2 = PersonForm(request.user, initial={"project": project})

		#address = person.get_absolute_url()
		#print(address)
		if person_id:
			person = get_object_or_404(Person, pk=person_id)

		#if request.method == 'POST':
		if request.method == 'POST':
			print("POST")
			form = PersonForm(request.user, request.POST, instance=person)
			if form.is_valid():
				item=form.save(commit=False)
				item.id = person_id
				item.project=project
				item.save()
				if not request.is_ajax():
					if person == None:
						print("added")
						messages.success(request, '"{t}" added successful.'.format(t=item.id))
					else:
						print("edited")
						messages.success(request, '"{t}" edited successful.'.format(t=item.id))

				#next = request.META('PATH_INFO')
				#print(next)
					#return HttpResponseRedirect(next)

				ser_item = serializers.serialize('json', [item,])
				print(ser_item)

				#return JsonResponse({"instance": ser_item}, status=200)
				return redirect("todo:project_details", project_id, project_slug)
		else:
			form = PersonForm(request.user, instance=person)
			print("GET")
		#else:
		#form = PersonForm(request.user, instance=person)

		#print(request.POST)
		context = {
			"project_id": project_id,
			"project_slug": project_slug,
			"person_id":person_id,
			"project": project,
			"hazards": hazards,
			"persons":persons,
			"form":form,
			"form1":form1,
			"form2":form2,
			"address":address

		}
		return render(request, "todo/project_details.html", context)
	# Show a specific list, ensuring permissions.
	raise PermissionDenied
