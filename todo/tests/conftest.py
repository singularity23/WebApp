import pytest

from django.contrib.auth.models import Group

from todo.models import Hazard, Project


@pytest.fixture
def todo_setup(django_user_model):
    # Two groups with different users, two sets of tasks.

    g1 = Group.objects.create(name="Workgroup One")
    u1 = django_user_model.objects.create_user(
        username="u1", password="password", email="u1@example.com", is_staff=True
    )
    u1.groups.add(g1)
    tlist1 = Project.objects.create(group=g1, name="Zip", slug="zip")
    Hazard.objects.create(description="u1", risk_level="High", project=tlist1)
    Hazard.objects.create(description="u1", risk_level="Low", project=tlist1)
    Hazard.objects.create(description="u1", risk_level="Medium", project=tlist1)

    g2 = Group.objects.create(name="Workgroup Two")
    u2 = django_user_model.objects.create_user(
        username="u2", password="password", email="u2@example.com", is_staff=True
    )
    u2.groups.add(g2)
    tlist2 = Project.objects.create(group=g2, name="Zap", slug="zap")
    Hazard.objects.create(description="u1", risk_level="High", project=tlist2)
    Hazard.objects.create(description="u1", risk_level="Low", project=tlist2)
    Hazard.objects.create(description="u1", risk_level="Medium", project=tlist2)

    # Add a third user for a test that needs two users in the same group.
    extra_g2_user = django_user_model.objects.create_user(
        username="extra_g2_user", password="password", email="extra_g2_user@example.com", is_staff=True
    )
    extra_g2_user.groups.add(g2)


@pytest.fixture()
# Set up an in-memory mail server to receive test emails
def email_backend_setup(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"