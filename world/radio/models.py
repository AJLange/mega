from django.db import models
from evennia import ObjectDB
from evennia.utils.idmapper.models import SharedMemoryModel
from django.contrib.postgres.fields import ArrayField

# radio channels



class Frequency(SharedMemoryModel):
    db_freq = models.IntegerField('Freq', Default=1)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    db_members = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_colorcode = models.CharField('Color', max_length=10, blank=True)
    db_name = models.CharField('Name', max_length=100, blank=True)
    db_gaglist = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_security_level = models.IntegerField('Security Level', Default=1)
    
    def __str__(self):
        return self.db_freq

class BufferMsg(SharedMemoryModel):
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    db_frequency = models.ForeignKey('Buffer', Frequency, blank=True)
    db_content = ArrayField((models.TextField(blank=True)), blank=True, size=50)

    def __str__(self):
        return self.db_frequency