from django.db import models
from evennia import ObjectDB
from django.utils import timezone
from evennia.utils.idmapper.models import SharedMemoryModel

# request database

class Request(models.Model):

    db_title = models.CharField('Title', max_length=200)
    db_submitter = models.CharField('Submitter', max_length=200, default="Player")
    db_message_body = models.TextField('Message Body')
    db_assigned_to = models.ForeignKey("objects.ObjectDB", related_name="Assigned_to", blank=True, null=True, on_delete=models.PROTECT)
    db_copied_to = models.ManyToManyField("objects.ObjectDB", related_name="Copied_to", blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    class RequestCategory(models.IntegerField):
        GENERAL = 1
        BUGFIX = 2
        CHARACTER = 3
        NEWS = 4
        BUILD = 5
        AUTO = 6
        RESEARCH = 7
        ACTIVITY = 8
        HELP = 9
        TYPE_CHOICES = (
            (GENERAL, 'General'),
            (BUGFIX, 'Bugfix'),
            (CHARACTER, 'Character'),
            (BUILD, 'Build'),
            (AUTO, 'Auto'),
            (NEWS, 'ICNews'),
            (RESEARCH, 'Research'),
            (ACTIVITY, 'Activity'),
            (HELP, 'HelpFile')
        )

    # The type of request
    type = models.IntegerField(
        choices=RequestCategory.TYPE_CHOICES
    )
    db_is_open = models.BooleanField('Open',default=True)
    

    def __str__(self):
        return self.db_title
    

# response to a request. Request can have multiple responses/back and forth
class RequestResponse(models.Model):
    db_text = models.TextField('Response',blank=True)
    db_author = models.ForeignKey("objects.ObjectDB", related_name="author", blank=True, null=True, on_delete=models.PROTECT)
    db_request = models.ForeignKey(Request, related_name="Request",blank=True, null=True, on_delete=models.PROTECT)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    db_was_read = models.BooleanField("Read", default=False)
    
