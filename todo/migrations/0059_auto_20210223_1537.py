# Generated by Django 3.1.5 on 2021-02-23 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0058_auto_20210223_0847'),
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