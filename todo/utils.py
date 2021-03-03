import email.utils
import logging
import os
import re
import time
from re import search, match

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core import mail
from django.template.loader import render_to_string
from simple_history.models import HistoricalChanges, HistoricalRecords
from todo.models import Comment, Hazard, Attachment, ControlMeasure, RiskLevel, Person
from todo.defaults import defaults
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

log = logging.getLogger(__name__)


def staff_check(user):
    """If TODO_STAFF_ONLY is set to True, limit view access to staff users only.
        # FIXME: More granular access control needed - see
        https://github.com/shacker/django-todo/issues/50
    """

    if defaults("TODO_STAFF_ONLY"):
        return user.is_staff
    else:
        # If unset or False, allow all logged in users
        return True


def user_can_read_hazard(hazard, user):
    return user.groups in user.groups.all() or user.is_superuser


def todo_get_backend(hazard):
    """Returns a mail backend for some hazard"""
    mail_backends = getattr(settings, "TODO_MAIL_BACKENDS", None)
    if mail_backends is None:
        return None

    hazard_backend = mail_backends[hazard.hazard_list.slug]
    if hazard_backend is None:
        return None

    return hazard_backend


def todo_get_mailer(user, hazard):
    """A mailer is a (from_address, backend) pair"""
    hazard_backend = todo_get_backend(hazard)
    if hazard_backend is None:
        return (None, mail.get_connection)

    from_address = getattr(hazard_backend, "from_address")
    from_address = email.utils.formataddr((user.username, from_address))
    return (from_address, hazard_backend)


def todo_send_mail(user, hazard, subject, body, recip_list):
    """Send an email attached to hazard, triggered by user"""
    references = Comment.objects.filter(hazard=hazard).only("email_message_id")
    references = (ref.email_message_id for ref in references)
    references = " ".join(filter(bool, references))

    from_address, backend = todo_get_mailer(user, hazard)
    message_hash = hash((subject, body, from_address, frozenset(recip_list), references))

    message_id = (
        # the hazard_id enables attaching back notification answers
        "<notif-{hazard_id}."
        # the message hash / epoch pair enables deduplication
        "{message_hash:x}."
        "{epoch}@django-todo>"
    ).format(
        hazard_id=hazard.pk,
        # avoid the -hexstring case (hashes can be negative)
        message_hash=abs(message_hash),
        epoch=int(time.time()),
    )

    # the thread message id is used as a common denominator between all
    # notifications for some hazard. This message doesn't actually exist,
    # it's just there to make threading possible
    thread_message_id = "<thread-{}@django-todo>".format(hazard.pk)
    references = "{} {}".format(references, thread_message_id)

    with backend() as connection:
        message = mail.EmailMessage(
            subject,
            body,
            from_address,
            recip_list,
            [],  # Bcc
            headers={
                **getattr(backend, "headers", {}),
                "Message-ID": message_id,
                "References": references,
                "In-reply-to": thread_message_id,
            },
            connection=connection,
        )
        message.send()


def send_notify_mail(new_hazard):
    """
    Send email to assignee if hazard is assigned to someone other than submittor.
    Unassigned hazards should not try to notify.
    """

    if new_hazard.assigned_to == new_hazard.created_by:
        return

    current_site = Site.objects.get_current()
    subject = render_to_string("todo/email/assigned_subject.txt", {"hazard": new_hazard})
    body = render_to_string(
        "todo/email/assigned_body.txt", {"hazard": new_hazard, "site": current_site}
    )

    recip_list = [new_hazard.assigned_to.email]
    todo_send_mail(new_hazard.created_by, new_hazard, subject, body, recip_list)


def send_email_to_thread_participants(hazard, msg_body, user, subject=None):
    """Notify all previous commentors on a hazard about a new comment."""

    current_site = Site.objects.get_current()
    email_subject = subject
    if not subject:
        subject = render_to_string("todo/email/assigned_subject.txt", {"hazard": hazard})

    email_body = render_to_string(
        "todo/email/newcomment_body.txt",
        {"hazard": hazard, "body": msg_body, "site": current_site, "user": user},
    )

    # Get all thread participants
    commenters = Comment.objects.filter(hazard=hazard)
    recip_list = set(ca.author.email for ca in commenters if ca.author is not None)
    for related_user in (hazard.created_by, hazard.assigned_to):
        if related_user is not None:
            recip_list.add(related_user.email)
    recip_list = list(m for m in recip_list if m)

    #todo_send_mail(user, hazard, email_subject, email_body, recip_list)


def toggle_hazard_completed(hazard_id: int) -> bool:
    """Toggle the `completed` bool on hazard from True to False or vice versa."""
    try:
        hazard = Hazard.objects.get(id=hazard_id)
        hazard.completed = not hazard.completed
        hazard.save()
        return True

    except Hazard.DoesNotExist:
        log.info(f"hazard {hazard_id} not found.")
        return False


def remove_attachment_file(attachment_id: int) -> bool:
    """Delete an Attachment object and its corresponding file from the filesystem."""
    try:
        attachment = Attachment.objects.get(id=attachment_id)
        if attachment.file:
            if os.path.isfile(attachment.file.path):
                os.remove(attachment.file.path)

        attachment.delete()
        return True

    except Attachment.DoesNotExist:
        log.info(f"Attachment {attachment_id} not found.")

        return False



def validate_project_number(request, project):

    project_number = project.cleaned_data['number']
    SAP_number = project.cleaned_data['SAP_id']
    print(project_number)
    if not re.match(r'^[A-Z]{2}-[A-Z]{2,3}-\d{3}$', project_number):
        messages.warning(request, "Project Number should follow format as SI-OKA-190, LM-MV-208, etc.")
        return False

    if not re.match(r'^[A-Z]{2}-\d{4}$', SAP_number):
        messages.warning(request,
            "SAP Number should follow format as DY-1943, DP-1526, etc.")
        return False

    return True

def get_history_change_reason(hazard):
    records = hazard.history.all()
    attrs = ['assigned_to', 'risk_level', 'control_measure', 'res_risk_level']
    labels = ["\"Assigned to\"", "\"Risk Level\"", "\"Control Measure\"", "\"Residual Risk\""]


    if records.exists():
        for record in records.iterator():
            prev = record.prev_record
            if prev is not None:
                change_field = None
                change_old = None
                change_new = None
                change_reason =[]
                delta = record.diff_against(prev)
                for change in (change for change in delta.changes if change.old != change.new and change_field != "Project" and change_field != "Index"):

                    if change.field not in attrs:
                        change_field = "\"" + change.field.capitalize() + "\""
                        msg = "%s content changed" % (change_field)
                        change_reason.append(msg)

                    else:
                        for x, y in zip(attrs, labels):
                            if x == change.field:
                                change_field = y
                                print(change_field)
                                if change.field == 'assigned_to' :
                                    if change.old is None:
                                        change_old = "None"
                                    else:
                                        change_old = "\"" + Person.objects.get(pk=change.old).full_name + "\""
                                    if change.new is None:
                                        change_new = "None"
                                    else:
                                        change_new = "\"" + Person.objects.get(pk=change.new).full_name + "\""

                                    msg = "%s changed from %s to %s" % (change_field, change_old, change_new)

                                elif change.field =='control_measure':

                                    if change.old is None:
                                        change_old = "None"
                                    else:
                                        print(ControlMeasure.objects.values_list('measure', flat=True).get(pk=change.old))
                                        change_old = "\"" + ControlMeasure.objects.values_list('measure', flat=True).get(pk=change.old) + "\""
                                    if change.new is None:
                                        change_new = "None"
                                    else:
                                        change_new = "\"" + ControlMeasure.objects.values_list('measure', flat=True).get(pk=change.new) + "\""
                                    msg = "%s changed from %s to %s" % (change_field, change_old, change_new)

                                elif search('risk_level', change.field):
                                    if change.old is None:
                                        change_old = "None"
                                    else:
                                        change_old = "\"" + RiskLevel.objects.values_list('level', flat=True).get(pk=change.old) + "\""
                                    if change.new is None:
                                        change_new = "None"
                                    else:
                                        change_new = "\"" + RiskLevel.objects.values_list('level', flat=True).get(pk=change.new) + "\""
                                    msg = "%s changed from %s to %s" % (change_field, change_old, change_new)

                        change_reason.append(msg)

                if change_reason != []:

                    record.history_change_reason = "; ".join(change_reason)
                    print(record.history_change_reason)
                    record.save()

    return records


def EGBC_folder(project):
    EGBC_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Engineering\Distribution\0 EGBC Filing\4 Projects"
    #EGBC_base = r"D:\documents"
    if project.region and project.location and project.number:
        EGBC_path = os.path.join(EGBC_base, str(project.region), str(project.location), project.number)
        try:
            if not os.path.exists(EGBC_path):
                os.makedirs(EGBC_path)
                print("folder created")
        except FileNotFoundError:
            print("folder not created")
        return EGBC_path

def SPOT_folder(project):

    SPOT_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Field Ops\SAM\Distribution Planning\System Improvement\SPOT Project Documentation"
    #SPOT_base = r"D:\documents"
    if project.number:
        SPOT_path = os.path.join(SPOT_base, project.number)

        return SPOT_path

def SBD_folder(project):
    SBD_base = r"\\bchydro.adroot.bchydro.bc.ca\data\Engineering\Distribution\0 EGBC Filing\4 Projects"

    if project.region and project.location and project.number:
        SBD_path = os.path.join(SBD_base, str(project.region), str(project.location), project.number, "Safety by Design")
        try:
            if not os.path.exists(SBD_path):
                os.makedirs(SBD_path)
                print("folder created")
        except FileNotFoundError:
            print("folder not created")
        return SBD_path

def PPM_folder(project):
    PPM_base = r"https://ppm.bchydro.bc.ca/projects/"
    if project.SAP_id:
        PPM_path = os.path.join(PPM_base, project.SAP_id)

        return PPM_path

def validate_sap_id(value):
    if match(r'^[A-Z]{2}-\d{4}$', value):
        return True

def validate_project_number(value):
    if match(r'^[A-Z]{2}-[A-Z]{2,3}-\d{3}$', value):
        return True
