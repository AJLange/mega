from django.db import models
from django.conf import settings
from evennia.utils.idmapper.models import SharedMemoryModel


# Create your models here.

class Roster(models.Model):

    db_name = models.CharField('Name', max_length=200)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    def __str__(self):
        return self.db_name

class PlayerAccount(SharedMemoryModel):
    """
    This is used to represent a player, who might be playing one or more Characters. 
    They're uniquely identified by their email address which is all we use for matching right now.
    """
    db_name = models.CharField('Nickname', max_length=120)
    email = models.EmailField(unique=True)
    gm_notes = models.TextField(blank=True, null=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    

    def __str__(self):
        return self.db_name
