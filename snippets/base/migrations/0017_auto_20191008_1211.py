# Generated by Django 2.2.6 on 2019-10-08 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0016_target_filtr_can_install_addons'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='metric_blocks',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='job',
            name='metric_clicks',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='job',
            name='metric_impressions',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='job',
            name='metric_last_update',
            field=models.DateTimeField(default='1970-01-01', editable=False, verbose_name='Last Update'),
        ),
    ]