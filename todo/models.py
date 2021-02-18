from __future__ import unicode_literals

import datetime
import os
import shutil
import textwrap
from django.core.validators import RegexValidator

from django.conf import settings
from django.contrib.auth.models import Group, User, BaseUserManager, AbstractBaseUser
from django.core import serializers
from django.db import DEFAULT_DB_ALIAS, models

from django.db.transaction import Atomic, get_connection
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from model_utils import Choices
from simple_history.models import HistoricalRecords
from django.utils.translation import ugettext_lazy as _


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

class LockedAtomicTransaction(Atomic):
    """
    modified from https://stackoverflow.com/a/41831049
    this is needed for safely merging

    Does a atomic transaction, but also locks the entire table for any transactions, for the duration of this
    transaction. Although this is the only way to avoid concurrency issues in certain situations, it should be used with
    caution, since it has impacts on performance, for obvious reasons...
    """

    def __init__(self, *models, using=None, savepoint=None):
        if using is None:
            using = DEFAULT_DB_ALIAS
        super().__init__(using, savepoint)
        self.models = models

    def __enter__(self):
        super(LockedAtomicTransaction, self).__enter__()

        # Make sure not to lock, when sqlite is used, or you'll run into
        # problems while running tests!!!
        if settings.DATABASES[self.using]["ENGINE"] != "django.db.backends.sqlite3":
            cursor = None
            try:
                cursor = get_connection(self.using).cursor()
                for model in self.models:
                    cursor.execute("LOCK TABLE {table_name}".format(
                        table_name=model._meta.db_table))
            finally:
                if cursor and not cursor.closed:
                    cursor.close()

class Stage(models.Model):
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
    level = models.CharField(max_length=60)

    def __str__(self):
        return self.level

    def color_text(self):

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

    color = property(color_text)
    print("color " + str(color))

    def IDtoLabel(id):
        if id != None:
            lvl = RiskLevel.objects.filter(id=id)[0]
            return str(lvl)
        else:
            return "None"

    class Meta:
        verbose_name_plural = "Risk Levels"


class ControlMeasure(models.Model):
    measure = models.CharField(max_length=60)

    #details = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.measure

    def IDtoLabel(id):
        if id != None:
            cm = ControlMeasure.objects.filter(id=id)[0]
            return str(cm)
        else:
            return "None"

    class Meta:
        verbose_name_plural = "Control Measures"


class Project(models.Model):
    """
    TODO: need to update the default links when using in Hydro enviorment

    """
    history = HistoricalRecords(cascade_delete_history=True)

    number = models.CharField(max_length=60, )
    slug = models.SlugField(default="")
    SAP_id = models.CharField(max_length=60, blank=True, null=True, )
    SPOT_link = models.CharField(max_length=240, blank=True, null=True)
    PPM_link = models.CharField(max_length=240, blank=True, null=True)
    EGBC_link = models.CharField(max_length=240, blank=True, null=True)
    SBD_link = models.CharField(max_length=240, blank=True, null=True)
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

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse("todo:project_details", kwargs={"project_id": self.pk, "project_slug": self.slug})

    @property
    def counts(self):
        return self.hazard_set.filter(res_risk_level=1).count() + self.hazard_set.filter(risk_level=1, control_measure=None).count()


    def slug_number(self):
        return slugify(self.number)

    slug = property(slug_number)

    @property
    def progress(self):
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

    def EGBC_folder(self):
        EGBC_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Engineering\Distribution\0 EGBC Filing\4 Projects"
        #EGBC_BASE = r"D:\documents"
        if self.region and self.location and self.number:
            EGBC_path = os.path.join(EGBC_BASE, str(self.region), str(self.location), self.number)
            if not os.path.exists(EGBC_path):
                os.makedirs(EGBC_path)
            return EGBC_path

    EGBC_path = property(EGBC_folder)


    def SPOT_folder(self):

        SPOT_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Field Ops\SAM\Distribution Planning\System Improvement\SPOT Project Documentation"
        #SPOT_base = r"D:\documents"
        if self.number:
            SPOT_path = os.path.join(SPOT_base, self.number)
            if not os.path.exists(SPOT_path):
                os.makedirs(SPOT_path)
            return SPOT_path

    SPOT_path = property(SPOT_folder)


    def SBD_folder(self):
        SBD_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Engineering\Distribution\0 EGBC Filing\4 Projects"

        if self.region and self.location and self.number:
            SBD_path = os.path.join(SBD_base, str(self.region), str(self.location), self.number, "Safety by Design")
            if not os.path.exists(SBD_path):
                os.makedirs(SBD_path)
            return SBD_path

    SBD_path = property(SBD_folder)

    def PPM_folder(self):
        PPM_base = r"https://ppm.bchydro.bc.ca/projects/"
        if self.SAP_id:
            PPM_path = os.path.join(PPM_base, self.SAP_id)

            return PPM_path

    PPM_path = property(PPM_folder)

    SPOT_link = SPOT_path
    EGBC_link = EGBC_path
    SBD_link = SBD_path
    PPM_link = PPM_path

class Person(models.Model):
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
