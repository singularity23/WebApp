# Generated by Django 3.1.5 on 2021-03-08 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0060_auto_20210308_0855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hazard',
            name='details',
            field=models.CharField(blank=True, max_length=360, null=True),
        ),
        migrations.AlterField(
            model_name='historicalhazard',
            name='details',
            field=models.CharField(blank=True, max_length=360, null=True),
        ),
    ]
