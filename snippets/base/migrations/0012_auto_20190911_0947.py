# Generated by Django 2.2.3 on 2019-09-11 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_auto_20190909_1027'),
    ]

    operations = [
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='DistributionBundle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('code_name', models.CharField(max_length=100, unique=True)),
                ('distributions', models.ManyToManyField(to='base.Distribution')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='distribution',
            field=models.ForeignKey(help_text='Set a Distribution for this Job. It should be normally left to Default. Useful for running Normandy experiments.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='jobs', to='base.Distribution'),
        ),
    ]