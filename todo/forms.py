import re
from django import forms
from django.contrib import messages, admin

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import ModelForm
from todo.models import ControlMeasure, Hazard, Person, Project, RiskLevel, Engagement, Region, Location, Stage
from todo.utils import EGBC_folder, SPOT_folder, SBD_folder, PPM_folder
from django.shortcuts import get_object_or_404, redirect, render
from todo.validators import validate_project_number, validate_sap_id
from urllib.parse import unquote, urlsplit, quote


class ProjectForm(ModelForm):
    """The picklist showing allowable groups to which a new list can be added
    determines which groups the user belongs to. This queries the form object
    to derive that list. """

    project_id = None

    def __init__(self, user, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        if kwargs.get("instance"):
            self.project_id = kwargs.get("instance").id

        self.initial['group'] = Group.objects.get(name="Engineer")
        print(self.initial['group'])

        self.fields["group"].widget.attrs = {
            "id"   : "id_group",
            "class": "custom-select mb-3",
            "name" : "group",
            }

        group_id = Group.objects.get(name="Engineer").id
        self.fields["POR"].queryset = User.objects.filter(groups=group_id)

        self.fields["POR"].widget.attrs = {
            "id"   : "id_POR",
            "class": "custom-select mb-3",
            "name" : "POR",
            }
        users = User.objects.all()
        self.fields["POR"].choices = [(user.pk, user.get_full_name()) for user in users]

        self.fields["region"].widget.attrs = {
            "id"   : "id_region",
            "class": "custom-select mb-3",
            "name" : "region",
            "onchange": "change_list()"
            }

        self.fields["location"].widget.attrs = {
            "id"   : "id_location",
            "class": "custom-select mb-3",
            "name" : "location",
            }
        self.fields['region'].queryset = Region.objects.all()

        self.fields["current_stage"].widget.attrs = {
            "id"   : "id_current_stage",
            "class": "custom-select mb-3",
            "name" : "current_stage",
            }
        self.fields['current_stage'].queryset = Stage.objects.all()
        self.fields['current_stage'].required = False

        project = get_object_or_404(Project, pk=self.project_id)

        self.initial['EGBC_link'] = unquote(EGBC_folder(project))
        self.initial['SBD_link'] = unquote(SBD_folder(project))
        self.initial['SPOT_link'] = unquote(SPOT_folder(project))
        self.initial['PPM_link'] = unquote(PPM_folder(project))

    region = forms.ModelChoiceField(queryset=Region.objects.all(), label=u'Region')

    location = forms.ModelChoiceField(queryset=Location.objects.all(), label=u'Location')
        # print("group:" + str(self.fields["group"].initial))

    SAP_id = forms.CharField(widget=forms.widgets.TextInput(), required=False,)

    number = forms.CharField(widget=forms.widgets.TextInput(), required=False,)

    title = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    project_scope = forms.CharField(widget=forms.Textarea(), required=False)
    in_service_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False)



    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        print("cleaned data:" + str(cleaned_data))
        number_passed = cleaned_data.get("number")
        SAP_passed = cleaned_data.get("SAP_id")
        print(self.project_id)
        qs = Project.objects.all()
        if self.project_id is None:
            if qs.filter(number=number_passed).exists() or qs.filter(SAP_id=SAP_passed).exists():
                raise ValidationError("project number or SAP number exists")

        print(validate_project_number(number_passed))
        if not validate_project_number(number_passed):
            self.add_error('number', 'invalid project number')

        if not validate_sap_id(SAP_passed):
            self.add_error('SAP_id', 'invalid SAP number')


    class Meta:
        model = Project
        exclude = ["slug", "SPOT_link", "PPM_link", "EGBC_link", "SBD_link"]


class ProjectLinkForm(ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(ProjectLinkForm, self).__init__(*args, **kwargs)
        if kwargs.get("instance"):
            self.project_id = kwargs.get("instance").id

        project = get_object_or_404(Project, pk=self.project_id)

        self.initial['EGBC_link'] = EGBC_folder(project)
        self.initial['SBD_link'] = SBD_folder(project)
        self.initial['SPOT_link'] = SPOT_folder(project)
        self.initial['PPM_link'] = PPM_folder(project)


    class Meta:
        model = Project
        fields = ["SPOT_link", "PPM_link", "EGBC_link", "SBD_link"]


class HazardForm(ModelForm):
    """The picklist showing the users to which a new task can be assigned
    must find other members of the group this TaskList is attached to."""
    project = None
    hazard = None
    def __init__(self, user, *args, **kwargs):
        super(HazardForm, self).__init__(*args, **kwargs)
        print(kwargs)
        # project_id = kwargs.get("project_id")

        if 'instance' in kwargs:
            self.hazard = kwargs.get("instance")
            self.project = self.hazard.project

            # print("instance: " + str(project))
        elif 'initial' in kwargs:
            self.project = kwargs.get("initial").get("project")
            # print("initial: " + str(project))
            hazards = Hazard.objects.filter(project=self.project)
            number = hazards.count()
            self.initial['index'] = number + 1

        p1 = Person.objects.filter(project=self.project)
        print(p1)
        self.fields["assigned_to"].queryset = p1.filter(is_team_member=True)

        self.fields["assigned_to"].widget.attrs = {
            "id"   : "id_assigned_to",
            "class": "custom-select mb-3",
            "name" : "assigned_to",
            }

        self.fields["risk_level"].queryset = RiskLevel.objects.all()
        self.fields["risk_level"].widget.attrs = {
            "id"   : "id_risk_level",
            "class": "custom-select mb-3",
            "name" : "risk_level",
            }

        self.fields["control_measure"].queryset = ControlMeasure.objects.all()
        self.fields["control_measure"].widget.attrs = {
            "id"   : "id_control_measure",
            "class": "custom-select mb-3",
            "name" : "control_measure",
            }
        self.fields["control_measure"].required = False
        self.fields["assigned_to"].requried = False
        self.fields["res_risk_level"].required = False
        # self.fields["res_risk_level"].initial = RiskLevel.objects.none

    description = forms.CharField(widget=forms.widgets.TextInput())

    note = forms.CharField(widget=forms.Textarea(), required=False)
    details = forms.CharField(widget=forms.Textarea(), required=False)

    # number = len(Hazard.objects.filter(project=project))

    class Meta:
        model = Hazard
        exclude = []


class PersonForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)

    first_name = forms.CharField(widget=forms.widgets.TextInput())
    last_name = forms.CharField(widget=forms.widgets.TextInput())
    Email = forms.EmailField(widget=forms.widgets.TextInput(), required=False)

    is_team_member = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(), required=False)
    is_stakeholder = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(), required=False)
    role = forms.CharField(widget=forms.widgets.TextInput())

    class Meta:
        model = Person
        exclude = []


class EngagementForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(EngagementForm, self).__init__(*args, **kwargs)

        project = kwargs.get("initial").get("project")
        p1 = Person.objects.filter(project=project)
        stakeholders = forms.ChoiceField(widget=forms.widgets.ChoiceWidget(choices=p1.filter(is_stakeholder=True)))
        self.fields["stakeholders"].queryset = p1.filter(is_stakeholder=True)
        self.fields["stakeholders"].widget.attrs = {
            "class": "form-control",
            "name": "stakeholders[]",
            "multiple": "multiple"
        }

    body = forms.CharField(widget=forms.Textarea(), required=False)

    class Meta:
        model = Engagement
        exclude = []


class AddExternalTaskForm(ModelForm):
    """Form to allow users who are not part of the GTD system to file a ticket."""

    title = forms.CharField(widget=forms.widgets.TextInput(
        attrs={"size": 35}), label="Summary")
    note = forms.CharField(widget=forms.widgets.Textarea(),
                           label="Problem Description")
    priority = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Hazard
        exclude = ("task_list",
                   "created_date",
                   "due_date",
                   "created_by",
                   "assigned_to",
                   "completed",
                   "completed_date",
                   "control_measure",
                   "risk_level",)


class SearchForm(forms.Form):
    """Search."""

    q = forms.CharField(widget=forms.widgets.TextInput(attrs={"size": 35}))


class UserCreationForm(ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    first_name = forms.CharField(widget=forms.widgets.TextInput())
    last_name = forms.CharField(widget=forms.widgets.TextInput())

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def validate_username(self):
        username = self.cleaned_data.get("email")
        if not (re.search("@bchydro.com", username)):
            return None
        else:
            return username

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            return None
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_staff')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'is_staff')
    list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()
