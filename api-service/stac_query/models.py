# Imports

# Django imports
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.gis.db import models
# Create your models here.

class stac(models.Model):
    type = models.CharField(max_length=50, blank=True, null=True)
    geometry_type = models.CharField(max_length=50)
    geometry_coordinates = models.GeometryField()
    beam_mode = models.CharField(max_length=50, null=True, blank=True)
    browse = models.URLField(max_length=500, null=True, blank=True)
    bytes = models.BigIntegerField(null=True, blank=True)
    center_lat = models.FloatField(null=True, blank=True)
    center_lon = models.FloatField(null=True, blank=True)
    file_id = models.CharField(max_length=100, unique=True)
    file_name = models.CharField(max_length=100, null=True, blank=True)
    flight_direction = models.CharField(max_length=10, null=True, blank=True)
    frame_number = models.IntegerField(null=True, blank=True)
    granuleType = models.CharField(max_length=50, null=True,blank=True)
    group_id = models.CharField(max_length=100, null=True, blank=True) 
    md5_sum = models.CharField(max_length=32, null=True, blank=True) 
    orbit = models.IntegerField(null=True, blank=True) 
    path_number = models.IntegerField(null=True, blank=True)
    pge_version = models.CharField(max_length=10, null=True, blank=True)
    platform = models.CharField(max_length=100, null=True, blank=True) 
    polarization = models.CharField(max_length=50, null=True, blank=True) 
    processing_date = models.DateField(null=True, blank=True) 
    processing_level = models.CharField(max_length=50, null=True, blank=True) 
    s3_urls = models.TextField(null=True, blank=True) 
    scene_name = models.CharField(max_length=200, null=True, blank=True)
    sensor = models.CharField(max_length=50, null=True, blank=True) 
    start_time = models.DateTimeField(null=True, blank=True) 
    stop_time = models.DateTimeField(null=True, blank=True) 
    url = models.URLField(max_length=500, null=True, blank=True)
    
    
    class Meta:
        db_table = 'stac'
        app_label = 'stac_query'
        # models = [
        #     models.Index(fields=['file_id'], name='idx_stac_file_id'),
        #     models.Index(fields=['start_time'], name='idx_stac_start_time'), 
        #     models.Index(fields=['platform'], name='idx_stac_platform'),
        #     models.Index(fields=['scene_name'], name='idx_stac_scene_name'),
        #     models.Index(fields=['center_lat', 'center_lon'], name='idx_stac_center_lat_lon'),
        # ]

    def __str__(self):
        return self.file_id
