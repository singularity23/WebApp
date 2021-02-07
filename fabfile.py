#TODO: Code this before releasing

from fabric.api import cd, env, run, sudo
from fabric.contrib.files import exists
from fabric.utils import abort

REPO_URL =
SITE_DIR = "/home/django/gtd"
env.user = "django"
env.hosts =


def deploy():
    """Call typical Django site deployment steps in order."""

    with cd(SITE_DIR):
        _update_source()
        _update_virtualenv()
        _update_static_files()
        _update_database()
        _restart_servers()


def _update_source():
    if exists(".git"):
        run("git checkout master")
        run("git pull origin master")
    else:
        current_dir = run("pwd")
        abort(f"{current_dir} does not appear to be a git directory. Exiting.")


def _update_virtualenv():
    run('pipenv install')


def _update_static_files():
    run("pipenv run ./manage.py collectstatic --noinput")


def _update_database():
    run("pipenv run ./manage.py migrate")


def _restart_servers():
    sudo("systemctl restart gunicorn")
    sudo("service nginx restart")
