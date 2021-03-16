import pytest

from django.contrib.auth.models import Group, User

from todo.models import Hazard, Project, MyUserManager

@pytest.fixture
def todo_setup(django_user_model):
    # Two groups with different users, two sets of tasks.

    g1 = Group.objects.create(name="g1")
    u1 = User.objects.create(username="u1@bchydro.com", email="u1@bchydro.com", password="password")
    g1.user_set.add(u1)
    project_1 = Project.objects.create(number="LM-VAN-111", SAP_id="TY-1111", title="ZIP", POR = u1)
    h1 = Hazard.create(description="u1", risk_level="High", project=project_1)
    h2 = Hazard.create(description="u1", risk_level="Low", project=project_1)
    h3 = Hazard.create(description="u1", risk_level="Medium", project=project_1)

    g2 = Group.objects.create(name="g2")
    u2 = User.objects.create(username="u1@bchydro.com", email="u2@bchydro.com", password="password")

    g2.user_set.add(u2)
    project_2 = Project.objects.create(number="LM-VAN-211", SAP_id="TY-2111", title="ZIP2", POR = u2)
    h4 = Hazard.create(description="u2", risk_level="High", project=project_2)
    h5 = Hazard.create(description="u2", risk_level="Low", project=project_2)
    h6 = Hazard.create(description="u2", risk_level="Medium", project=project_2)

    # Add a third user for a test that needs two users in the same group.
    extra_g2_user = MyUserManager.create_user(email="extra_g2_user@bchydro.com", password="password")
    g2.user_set.add(extra_g2_user)


@pytest.fixture
# Set up an in-memory mail server to receive test emails
def email_backend_setup(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
