# Generated by Django 3.1.4 on 2020-12-04 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0015_auto_20201204_1227'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stakeholder',
            name='project',
        ),
        migrations.RemoveField(
            model_name='stakeholder',
            name='rep',
        ),
        migrations.AddField(
            model_name='person',
            name='is_stakeholder',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='person',
            name='is_team_member',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='person',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='todo.project'),
        ),
        migrations.AlterField(
            model_name='person',
            name='department',
            field=models.CharField(max_length=60, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='position',
            field=models.CharField(max_length=60, null=True),
        ),
        migrations.DeleteModel(
            name='ProjectMember',
        ),
        migrations.DeleteModel(
            name='Stakeholder',
        ),
    ]
