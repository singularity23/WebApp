from __future__ import unicode_literals

import datetime
import os
import shutil
import textwrap

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, User
from django.core import serializers
from django.core.validators import RegexValidator
from django.db import DEFAULT_DB_ALIAS, models
from django.db.transaction import Atomic, get_connection
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from simple_history.models import HistoricalRecords
from urllib.parse import unquote, urlsplit, quote



def get_attachment_upload_dir(instance, filename):
    """Determine upload dir for hazard attachment files.
    """
    path = "hazard_" + str(instance.hazard.id)
    newpath = os.path.join(str(instance.hazard.project.id), path, "attachments", filename)
    return newpath

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

class MyUser(AbstractBaseUser):
    """
    creating user
    """
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()
    username = None
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_staff

class Stage(models.Model):
    """
    model for project stages
    """
    NAME = Choices(
        ('Definition'),
        ('Detailed Design'),
        ('Construction'),
        ('Close Out'),
   )

    name = models.CharField(
       max_length=60,
       choices=NAME,
   )

    def __str__(self):
        return self.name


class Region(models.Model):
    """
    model for regions in DE
    """
    NAME = Choices(
        ('VI'),
        ('Interior & NIA'),
        ('LMN'),
        ('LMS'),
   )

    name = models.CharField(
       max_length=60,
       choices=NAME,
   )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "regions"

class Location(models.Model):
    """
    model for locations under each region
    """
    NAME = Choices(
        ('VI', ('Victoria & Saanich', 'Western Communities', 'Duncan & Gulf Islands', 'Central VI', 'Northern VI')),
        ('Interior & NIA', ('Northern Interior', 'Southern Interior')),
        ('LMN', ('Vancouver', 'Burnaby', 'North Shore')),
        ('LMS', ('Fraser Valley West', 'Fraser Valley East')),
   )

    name = models.CharField(max_length=60, choices=NAME)
    region = models.ForeignKey(Region, related_name="locations", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "locations"

class RiskLevel(models.Model):
    """
    model for risk levels
    """
    level = models.CharField(max_length=60)

    def __str__(self):
        return self.level

    def color_text(self):
        """
        Color code risk levels for highlighting
        """
        if self.level == "High":
            return "negative"
        elif self.level == "Medium":
            return "warning"
        elif self.level == "Low":
            return "positive-warning"
        elif self.level == "None":
            return "positive"
        else:
            print("error")
            return ""

    class Meta:
        verbose_name_plural = "Risk Levels"

    color = property(color_text)
    print("color " + str(color))

class ControlMeasure(models.Model):
    measure = models.CharField(max_length=60)
    """model for control measures"""
    #details = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.measure
    class Meta:
            verbose_name_plural = "Control Measures"

class Project(models.Model):
    """
    TODO: need to update the default links when using in Hydro sever

    """
    history = HistoricalRecords(cascade_delete_history=True)

    number = models.CharField(max_length=60, )
    slug = models.SlugField(default="")
    SAP_id = models.CharField(max_length=60, blank=True, null=True, )

    title = models.CharField(max_length=140, blank=True, null=True)
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, blank=False, null=True, )

    project_scope = models.TextField(blank=True, null=True)
    in_service_date = models.DateField(blank=True, null=True)
    current_stage = models.ForeignKey(Stage,
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,)
    region = models.ForeignKey(Region,
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,)
    location = models.ForeignKey(Location,
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,)
    POR = models.ForeignKey(settings.AUTH_USER_MODEL,
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL,)

    SPOT_link = models.CharField(max_length=240, blank=True, null=True,)
    PPM_link = models.CharField(max_length=240, blank=True, null=True, )
    EGBC_link = models.CharField(max_length=240, blank=True, null=True, )
    SBD_link = models.CharField(max_length=240, blank=True, null=True, )

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        """
        Get project specific url
        """
        return reverse("todo:project_details", kwargs={"project_id": self.pk, "project_slug": self.slug})

    @property
    def counts(self):
        """
        Count high risk items
        """
        return self.hazard_set.filter(res_risk_level=1).count() + self.hazard_set.filter(risk_level=1, control_measure=None).count()



    def slug_number(self):
        return slugify(self.number)

    slug = property(slug_number)

    @property
    def progress(self):
        """
        Get project progress
        """
        portion = 0
        stages = Stage.objects.all()
        length = len(stages)
        if self.current_stage:
            portion = self.current_stage.id * 100 / length
        print("portion"+ str(portion))
        return portion
    class Meta:
        ordering = ["POR", "number"]
        verbose_name_plural = "Projects"

class Person(models.Model):
    """
    Model for team members and stakeholders
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=60, blank=True, null=True)
    last_name = models.CharField(max_length=60, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)
    is_team_member = models.BooleanField(default=False)
    is_stakeholder = models.BooleanField(default=False)
    role = models.CharField(max_length=60, null=True)

    def get_absolute_url(self):
        return reverse("todo:team_edit", kwargs={"project_id": self.project.pk, "project_slug": self.project.slug, "person_id": self.pk})

    def __str__(self):
        return '%s %s (%s)' % (self.first_name, self.last_name, self.role)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    @classmethod
    def create(cls, project, first_name, last_name, Email, is_team_member, is_stakeholder, role):
        new_person = cls(project=project, first_name=first_name, last_name=last_name, Email=Email, is_team_member=is_team_member, is_stakeholder=is_stakeholder, role=role)
        # do something with the book
        return new_person
    class Meta:
        unique_together = ["project", "first_name", "last_name"]

class Hazard(models.Model):
    history = HistoricalRecords(cascade_delete_history=True)
    index = models.IntegerField(blank=True, null=True,)
    description = models.CharField(max_length=140)
    risk_level = models.ForeignKey(RiskLevel, on_delete=models.CASCADE,
                                   blank=True, null=True,
                                   related_name="risk_level")
    control_measure = models.ForeignKey(
        ControlMeasure, on_delete=models.CASCADE, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    # residual = models.ForeignKey(RiskLevel, on_delete=models.CASCADE,
    # blank=True, null=True,
    # related_name = "residual")
    res_risk_level = models.ForeignKey(RiskLevel, on_delete=models.CASCADE,
                                       blank=True, null=True,
                                       related_name="res_risk_level", )
    project = models.ForeignKey(
        Project, blank=True, null=True, on_delete=models.CASCADE,)

    assigned_to = models.ForeignKey(Person,
                                    blank=True,
                                    null=True,
                                    related_name="todo_assigned_to",
                                    on_delete=models.CASCADE,
                                    )

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("todo:hazard_details", kwargs={"project_id": self.project.id, "project_slug": self.project.slug, "hazard_id": self.id})

    def POR_fullname(self):
        return self.assigned_to.get_full_name

    def res_risk(self):
        mx_res = [(4, 3, 2, 2, 1), (4, 3, 3, 2, 2),
                  (4, 3, 3, 3, 3), (4, 4, 4, 4, 4)]

        if self.risk_level != None:

            if self.control_measure:

                return mx_res[self.risk_level.id - 1][self.control_measure.id - 1]
            else:
                return self.risk_level.id

    res_idex = property(res_risk)
    print("res_idex" + str(res_idex))

    def get_res_risk(self):
        if self != None:
            return RiskLevel.objects.values_list('level', flat=True).get(id=self.res_idex)

    res_level = property(get_res_risk)
    print("res_level" + str(res_level))

    def color_text(self):

        if self.res_idex == 1:
            return "negative"
        elif self.res_idex == 2:
            return "warning"
        elif self.res_idex == 3:
            return "positive-warning"
        elif self.res_idex == 4:
            return "positive"
        else:
            return ""
            print("error")

    color = property(color_text)

    def project_subfolder(self):
        PATH = os.path.join(("hazard_"+str(self.pk)), "attachments")
        return PATH

    path = property(project_subfolder)

    def export(self):
        objects = Hazard.objects.filter(project = self.project)

        filename = os.path.join(settings.BASE_DIR, "hazard.json")
        print(filename)
        file = open(filename, "w")
        serialized = serializers.serialize("json", objects)
        print(serialized)
        file.write(serialized)
        file.close()

    def counts(self):
        hazards = Hazard.objects.filter(project=self.project)
        print(hazards)
        return (hazards.count())

    number = property(counts)

    class Meta:
        verbose_name_plural = "hazards"
        unique_together = ['index','project']
        # Prevents (at the database level) creation of two lists with the same
        # slug in the same group

class Engagement(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    stakeholders = models.ManyToManyField(Person, db_table="todo_engagement_stakeholders")
    date = models.DateTimeField(default=datetime.datetime.now)
    body = models.TextField(blank=True)
    stakeholders_string = models.TextField(blank=True)

    class Meta:
        ordering =['date']



class Comment(models.Model):
    """
    Not using Django's built-in comments because we want to be able to save
    a comment and change details at the same time. Rolling our own since it's easy.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(default=datetime.datetime.now)
    email_from = models.CharField(max_length=320, blank=True, null=True)
    email_message_id = models.CharField(max_length=255, blank=True, null=True)

    body = models.TextField(blank=True)

    class Meta:
        # an email should only appear once per task
        unique_together = ("hazard", "email_message_id")
        ordering = ["date"]


    @property
    def author_text(self):
        if self.author is not None:
            return '%s %s' % (self.author.first_name, self.author.last_name)

        assert self.email_message_id is not None
        return str(self.email_from)

    @property
    def snippet(self):
        body_snippet = textwrap.shorten(self.body, width=35, placeholder="...")
        # Define here rather than in __str__ so we can use it in the admin
        # list_display
        return "{author} - {snippet}...".format(author=self.author_text, snippet=body_snippet)

    def __str__(self):
        return self.snippet


class Attachment(models.Model):
    """
    Defines a generic file attachment for use in M2M relation with Task.
    """

    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, blank=True, null=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    file = models.FileField(
        upload_to=get_attachment_upload_dir, max_length=255,)

    def filename(self):
        return os.path.basename(self.file.name)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def __str__(self):
        return f"{self.file.name}"

    def save_to_local(self, project, hazard):
        p = project.SBD_path
        h = hazard.path
        f = self.filename()
        dst = os.path.join(p, h)
        if not os.path.exists(dst):
            os.makedirs(dst)

        src = os.path.join(getattr(settings, 'MEDIA_ROOT', None), get_attachment_upload_dir(self, f))
        shutil.copy(src,dst)
        print (self.file.url)


class Data(models.Model):
    file_id = models.AutoField(primary_key=True)
    file = models.FileField(null=True, max_length=255)
    date_created = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return str(self.file.name)
