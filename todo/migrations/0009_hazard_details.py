# Generated by Django 3.1.3 on 2020-11-30 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0008_auto_20201129_0813'),
    ]

    operations = [
        migrations.AddField(
            model_name='hazard',
            name='details',
            field=models.TextField(blank=True, null=True),
        ),
    ]
