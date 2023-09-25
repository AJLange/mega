from django.db import models
from django.conf import settings
from evennia.utils.idmapper.models import SharedMemoryModel


# Create your models here.


class GameRoster(models.Model):
    """
    This contains a list of all valid 'games' for the purposes of categorizing
    player roster entries. 

    """
    db_name = models.CharField('Name', max_length=200)
    db_members = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    

    def __str__(self):
        return self.db_name