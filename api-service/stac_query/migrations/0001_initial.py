# Generated by Django 5.1.6 on 2025-03-04 07:39

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='stac',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, max_length=50, null=True)),
                ('geometry_type', models.CharField(max_length=50)),
                ('geometry_coordinates', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('beam_mode', models.CharField(blank=True, max_length=50, null=True)),
                ('browse', models.URLField(blank=True, max_length=500, null=True)),
                ('bytes', models.BigIntegerField(blank=True, null=True)),
                ('center_lat', models.FloatField(blank=True, null=True)),
                ('center_lon', models.FloatField(blank=True, null=True)),
                ('file_id', models.CharField(max_length=100, unique=True)),
                ('file_name', models.CharField(blank=True, max_length=100, null=True)),
                ('flight_direction', models.CharField(blank=True, max_length=10, null=True)),
                ('frame_number', models.IntegerField(blank=True, null=True)),
                ('granuleType', models.CharField(blank=True, max_length=50, null=True)),
                ('group_id', models.CharField(blank=True, max_length=100, null=True)),
                ('md5_sum', models.CharField(blank=True, max_length=32, null=True)),
                ('orbit', models.IntegerField(blank=True, null=True)),
                ('path_number', models.IntegerField(blank=True, null=True)),
                ('pge_version', models.CharField(blank=True, max_length=10, null=True)),
                ('platform', models.CharField(blank=True, max_length=100, null=True)),
                ('polarization', models.CharField(blank=True, max_length=50, null=True)),
                ('processing_date', models.DateField(blank=True, null=True)),
                ('processing_level', models.CharField(blank=True, max_length=50, null=True)),
                ('s3_urls', models.TextField(blank=True, null=True)),
                ('scene_name', models.CharField(blank=True, max_length=200, null=True)),
                ('sensor', models.CharField(blank=True, max_length=50, null=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('stop_time', models.DateTimeField(blank=True, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
            ],
            options={
                'db_table': 'stac',
            },
        ),
    ]
