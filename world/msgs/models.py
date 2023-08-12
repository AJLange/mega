from django.db import models


class Mail(models.Model):

    db_title = models.CharField('Subject', max_length=120)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    
    db_sender = models.CharField("Sender", blank=True, max_length=120)
    db_reciever = models.CharField("Receiver", blank=True, max_length=120)

    db_body = models.TextField('Message Body')


    def __str__(self):
        return self.db_title
