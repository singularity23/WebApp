from django import forms
from django.contrib import messages

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import ModelForm
from todo.validators import validate_project_number, validate_sap_id
from todo.models import ControlMeasure, Hazard, Person, Project, RiskLevel, Engagement, Region, Location, Stage

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

        #self.fields['location'].queryset = Location.objects.none()

        #if 'location' in self.data:
            #try:
            #    region_id = int(self.data.get('region'))
            #    self.fields['location'].queryset = Location.objects.filter(region_id=region_id).order_by('name')
          #  except (ValueError, TypeError):
         #       pass  # invalid input from the client; ignore and fallback to empty City queryset

      #  elif self.instance.pk:
     #       self.fields['location'].queryset = self.instance.region.locations.order_by('name')


        region = forms.ModelChoiceField(queryset=Region.objects.all(), label=u'Region')

        #for obj in self.fields['region'].queryset:
            #if region == obj:
                #location = forms.ModelChoiceField(queryset=self.region.locations.all(), label=u'Location')

        location = forms.ModelChoiceField(queryset=Location.objects.all(), label=u'Location')

        # print("group:" + str(self.fields["group"].initial))

    SAP_id = forms.CharField(widget=forms.widgets.TextInput(), required=False,)

    number = forms.CharField(widget=forms.widgets.TextInput(), required=False,)

    title = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    project_scope = forms.CharField(widget=forms.Textarea(), required=False)
    in_service_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False)

    SPOT_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)
    PPM_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)
    EGBC_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)
    SBD_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)

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

    SPOT_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)
    PPM_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)

    EGBC_link = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    SBD_link = forms.CharField(
        widget=forms.widgets.TextInput(), required=False)

    class Meta:
        model = Project
        fields = ["SPOT_link", "PPM_link", "EGBC_link", "SBD_link"]


class HazardForm(ModelForm):
    """The picklist showing the users to which a new task can be assigned
    must find other members of the group this TaskList is attached to."""
    project = None

    def __init__(self, user, *args, **kwargs):
        super(HazardForm, self).__init__(*args, **kwargs)
        print(kwargs)
        # project_id = kwargs.get("project_id")

        if 'instance' in kwargs:
            hazard = kwargs.get("instance")
            self.project = hazard.project

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
            "class": "custom-select custom-select-sm mb-3",
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


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    def clean_email(self):
        data = self.cleaned_data['email']
        if "@bchydro.com" not in data:
            raise ValidationError("Only BCH Email is allowed")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',)
