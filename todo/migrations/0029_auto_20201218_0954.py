# Generated by Django 3.1.4 on 2020-12-18 09:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0028_auto_20201216_2103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalproject',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='project',
            name='slug',
        ),
    ]
