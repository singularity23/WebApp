# Generated by Django 3.1.4 on 2020-12-15 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0025_auto_20201215_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalproject',
            name='EGBC_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='PPM_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='SBD_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='SPOT_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='EGBC_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='PPM_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='SBD_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='SPOT_link',
            field=models.CharField(blank=True, max_length=240, null=True),
        ),
    ]
