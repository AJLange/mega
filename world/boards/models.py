from django.db import models
from world.pcgroups.models import PlayerGroup

# Create your models here.

class BulletinBoard(models.Model):

    db_name = models.CharField('Board Name',max_length=120)
    db_groups = models.ManyToManyField(PlayerGroup, blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    has_subscriber = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_timeout = models.IntegerField('Timeout', blank=True, default=180)

    def __str__(self):
        return self.db_name


class BoardPost(models.Model):

    db_title = models.CharField('Post Title',max_length=360)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    db_board = models.ForeignKey(BulletinBoard, on_delete=models.CASCADE)
    posted_by = models.CharField('Author',max_length=120)
    body_text = models.TextField('Post')
    read_by = models.ManyToManyField("objects.ObjectDB", blank=True)
    is_pinned = models.BooleanField('Is Pinned?', default=False)

    def __str__(self):
        return self.db_title