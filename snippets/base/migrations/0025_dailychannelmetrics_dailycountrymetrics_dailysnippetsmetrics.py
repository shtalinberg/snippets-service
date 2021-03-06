# Generated by Django 2.2.6 on 2019-12-04 18:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0024_auto_20191119_1424'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyCountryMetrics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_fetched_on', models.DateTimeField(auto_now_add=True)),
                ('country', models.CharField(max_length=255)),
                ('date', models.DateField(editable=False)),
                ('impressions', models.PositiveIntegerField(default=0, editable=False)),
                ('clicks', models.PositiveIntegerField(default=0, editable=False)),
                ('blocks', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'verbose_name_plural': 'Daily Country Metrics',
                'unique_together': {('country', 'date')},
            },
        ),
        migrations.CreateModel(
            name='DailyChannelMetrics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_fetched_on', models.DateTimeField(auto_now_add=True)),
                ('channel', models.CharField(max_length=255)),
                ('date', models.DateField(editable=False)),
                ('impressions', models.PositiveIntegerField(default=0, editable=False)),
                ('clicks', models.PositiveIntegerField(default=0, editable=False)),
                ('blocks', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'verbose_name_plural': 'Daily Channel Metrics',
                'unique_together': {('channel', 'date')},
            },
        ),
        migrations.CreateModel(
            name='DailySnippetsMetrics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_fetched_on', models.DateTimeField(auto_now_add=True)),
                ('date', models.DateField(editable=False)),
                ('impressions', models.PositiveIntegerField(default=0, editable=False)),
                ('clicks', models.PositiveIntegerField(default=0, editable=False)),
                ('blocks', models.PositiveIntegerField(default=0, editable=False)),
                ('snippet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='base.ASRSnippet')),
            ],
            options={
                'verbose_name_plural': 'Daily Snippets Metrics',
                'unique_together': {('snippet', 'date')},
            },
        ),
    ]
