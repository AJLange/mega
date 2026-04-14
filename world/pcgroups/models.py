from django.db import models
from evennia import ObjectDB
from django.urls import reverse
from django.utils.text import slugify

# Storage of groups for PCs

class PlayerGroup(models.Model):

    db_name = models.CharField('Group Name', max_length=100)
    db_leader = models.CharField('Leader', max_length=120)
    db_twoic = models.CharField('Secondary Leader', max_length=120, null=True, blank=True)
    db_description = models.TextField('Description',blank=True)
    db_color = models.CharField('Color', max_length=20, blank=True)
    db_radio_a = models.CharField('Radio A',max_length=10, null=True, blank=True)
    db_radio_b = models.CharField('Radio B',max_length=10, null=True, blank=True)
    db_motd = models.TextField('Message of the Day',blank=True)
    db_members = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    def __str__(self):
        return self.db_name
    
    def web_get_detail_url(self):
        try:
            return reverse(
                "%s-detail" % slugify(self._meta.verbose_name),
                kwargs={"category": slugify(self.db_help_category), "topic": slugify(self.db_key)},
            )
        except Exception:
            return "#"

class Squad(models.Model):

    db_name = models.CharField('Squad Name', max_length=100)
    db_leader = models.CharField('Leader', max_length=120)
    db_orders = models.TextField('Orders',blank=True)
    db_members = models.ManyToManyField("objects.ObjectDB", blank=True)
    db_group = models.ForeignKey(PlayerGroup, blank=True, null=True, on_delete=models.CASCADE)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    def __str__(self):
        return self.db_name



