# Generated by Django 3.1.5 on 2021-02-04 23:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0055_auto_20210127_2242'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Definition', 'Definition'), ('Detailed Design', 'Detailed Design'), ('Construction', 'Construction'), ('Close Out', 'Close Out')], max_length=60)),
            ],
        ),
        migrations.RemoveField(
            model_name='historicalproject',
            name='stage',
        ),
        migrations.RemoveField(
            model_name='project',
            name='stage',
        ),
        migrations.AddField(
            model_name='historicalproject',
            name='current_stage',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='todo.stage'),
        ),
        migrations.AddField(
            model_name='project',
            name='current_stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='todo.stage'),
        ),
    ]
