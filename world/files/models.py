from django.db import models
from evennia import ObjectDB
from django.utils import timezone
from evennia.utils.idmapper.models import SharedMemoryModel

# request database

class Topic(SharedMemoryModel):
    db_name = models.CharField('Name', max_length=2000)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    def __str__(self):
        return self.db_name

class Keyword(SharedMemoryModel):
    db_keyword = models.CharField('Keyword', max_length=200, unique = True)
   
    def __str__(self):
        return self.db_keyword

class File(SharedMemoryModel):
    db_title = models.CharField('Name', max_length=200)
    db_text = models.TextField('File',blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    db_author = models.CharField('Author', max_length=200)
    up_to_date = models.BooleanField('Up to date?', default=True)
    db_topic = models.ForeignKey(Topic, blank=True, null=True, on_delete=models.PROTECT)
    db_keywords = models.ManyToManyField(Keyword, blank=True)

    def __str__(self):
        return self.db_title