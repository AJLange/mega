from django.db import models
from django.conf import settings
from evennia.utils.idmapper.models import SharedMemoryModel
from world.combat.models import Weapon, BusterList

# Create your models here.

class Capability(SharedMemoryModel):

    db_name = models.CharField('Name',max_length=200)
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    def __str__(self):
        return self.db_name
'''
Mode Swap messages:

Mode: '<player> has activated <pronoun>'s <name> mode!'
Stance: '<player> has swapped to <pronoun>'s <name> stance!'
Focus: '<player> focuses <pronoun>'s efforts, becoming <name>!'
Form: '<player> changes forms, becoming <pronoun>'s <name>!'
VR: '<player> jacks in, activating <name>!'
Summon: '<player> summons <name> to assist!'
Minion: '<player> is playing as squadron <name>.'
System: '<player> activates <pronoun>'s <name> system!'
Armor: '<player>' activates <pronoun>'s <name> armor!'
'''

class ArmorMode(SharedMemoryModel):
    # armor mode object for holding stats

    db_name = models.CharField('Name', max_length=255)

    db_belongs_to = models.CharField('Belongs to', max_length=255, default="None")
    db_is_stolen = models.BooleanField('Is Stolen?', default=False)
    #todo: autopopulate this. fine for now.
    db_time_out = models.DateTimeField('time out',blank=True, null=True)

    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)

    class ModeSwap(models.IntegerField):
        MODE = 1
        STANCE = 2
        FOCUS = 3
        FORM = 4
        VR = 5
        SUMMON = 6
        MINION = 7
        SYSTEM = 8
        ARMOR = 9
        TYPE_CHOICES = (
            (MODE, 'Mode'),
            (STANCE, 'Stance'),
            (FOCUS, 'Focus'),
            (FORM, 'Form'),
            (VR, 'VR'),
            (SUMMON, 'Summon'),
            (MINION, 'Minion'),
            (SYSTEM, 'System'),
            (ARMOR, 'Armor'),
        )
    db_swap = models.IntegerField('Swap Style',
        choices=ModeSwap.TYPE_CHOICES,default=1
    )
    
    #stats   
    
    db_pow = models.IntegerField('Power', default=1)
    db_dex = models.IntegerField('Dexterity', default=1)
    db_ten = models.IntegerField('Tenacity', default=1)
    db_cun = models.IntegerField('Cunning', default=1)
    db_edu = models.IntegerField('Education', default=1)
    db_chr = models.IntegerField('Charisma', default=1)
    db_aur = models.IntegerField('Aura', default=1)

    db_size = models.CharField('Size',blank=True,null=True, max_length=40)
    db_speed = models.IntegerField('Speed',default=1)
    db_strength = models.CharField('Strength',blank=True,null=True, max_length=40)

    db_resistance = models.CharField('Resistance',blank=True,null=True, max_length=100)
    db_weakness = models.CharField('Weakness',blank=True,null=True, max_length=100)
    
    #abilities    

    db_discern = models.IntegerField('Discern', default=1)
    db_aim = models.IntegerField('Aim', default=1)
    db_athletics = models.IntegerField('Athletics', default=1)
    db_force =  models.IntegerField('Force', default=1)
    db_mechanics = models.IntegerField('Mechanics', default=1)
    db_medicine =  models.IntegerField('Medicine', default=1)
    db_computer = models.IntegerField('Computer', default=1)
    db_stealth = models.IntegerField('Stealth', default=1) 
    db_heist = models.IntegerField('Heist', default=1)
    db_convince = models.IntegerField('Convince', default=1)
    db_presence = models.IntegerField('Presence', default=1)
    db_arcana = models.IntegerField('Arcana', default=1)

    # capabilities as secondary data field for extensibility
    
    db_capabilities = models.ManyToManyField(Capability, blank=True)
    db_weapons = models.ManyToManyField(Weapon, blank=True)
    db_busterlist = models.ManyToManyField(BusterList, blank=True)

    db_primary = models.ForeignKey(Weapon, on_delete=models.PROTECT, blank=True, related_name='primary_weapon')
    db_secondary = models.ForeignKey(Weapon, on_delete=models.PROTECT, blank=True, related_name='secondary_weapon')


    def __str__(self):
        return self.db_name