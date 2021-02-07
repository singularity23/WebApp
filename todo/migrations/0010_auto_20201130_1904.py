# Generated by Django 3.1.3 on 2020-11-30 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0009_hazard_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hazard',
            name='control_measure',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='todo.controlmeasure'),
        ),
        migrations.AlterField(
            model_name='hazard',
            name='risk_level',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='todo.risklevel'),
        ),
    ]
