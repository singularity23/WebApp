# Generated by Django 3.1.5 on 2021-01-11 10:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0045_auto_20210111_1036'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproject',
            name='location',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='todo.location'),
        ),
        migrations.AddField(
            model_name='historicalproject',
            name='region',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='todo.region'),
        ),
        migrations.AddField(
            model_name='project',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='todo.location'),
        ),
        migrations.AddField(
            model_name='project',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='todo.region'),
        ),
    ]
