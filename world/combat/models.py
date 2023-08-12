from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from django.test.utils import override_settings


'''
WeaponClasses determine which roll of dice is used to hit 
with this attack.
'''

class WeaponClass(models.IntegerField):
        RANGED = 1
        WAVE = 2
        THROWN = 3

        MELEE = 4
        BLITZ = 5
        SNEAK= 6
        GRAPPLE = 7

        SPELL = 8
        WILL = 9
        
        GADGET = 10
        CHIP = 11
        RANDOM = 12
        
        TYPE_CHOICES = (
            (RANGED, 'Ranged'),
            (WAVE, 'Wave'),
            (THROWN, 'Thrown'),
            (MELEE, 'Melee'),
            (BLITZ, 'Blitz'),
            (SNEAK, 'Sneak'),
            (GRAPPLE, 'Grapple'),
            (SPELL, 'Spell'),
            (WILL, 'Will'),
            (GADGET, 'Gadget'),
            (CHIP, 'Chip'),
            (RANDOM, 'Random'),
        )


'''
Types are per-weapon not per-character, but some characters only have certain weapons. 
This is closer to an older paradigm of being able to have whatever elements.

Slashing: Things intended to cut you. This includes beam-based melee weapons. 
    This is swords, but not arrows or armor piercing weapons.
Piercing: Things intended to pierce. This is things like Needle Cannon or a bow and arrow. 
    Some swords may fall in this category but not most.
Electric: Electromagnetic disturbances. Lightning out of the hands.
Explosive: Damage primarily caused by explosive force. Bombs, rockets,  grenades.
Fire: Intense thermal energy intended to burn or melt. Flamethrowers, incendiary mines.
Gravity: Gravity and magnetic energy fields.
Air: Wind stuff. Air is back, baby.
Ice: The removal of thermal energy intended to freeze or slow. Cryogenic blasts. Ice rays.
Toxic: Things that are liquids but are not water that cause harm by their inherent properties. 
    Sludge, ooze, goop, oils. Renaming this away from corrosive because not all chemical attacks 
    were corrosive. Renaming this from Chemical because Toxic is more evocative. 
    This is not a final change.
Blunt: Blunt force trauma from a heavy thing. Hammers.
Quake: Earth stuff that is the earth shaking, not blunt force trauma. Dirt and Rock stuff.
Karate: The using of martial arts as a weapon specifically. 
Sonic: Damage caused by sound waves or focused atmospheric oscillations. Very loud noises. Bad karaoke. 
Time: Attacks that mess with time. Timestopper. Ragtime.
Wood: Attacking with a plant. It's not necessarily wood, but sometimes it's wood.
Water: Water or a non-corrosive water-like fluid primarily used to inflict harm. Water cannons. Tidal waves.
Plasma: Lemons from the energy cannon. Most lightsabers. 
Laser: Attacks that are based on mundane light, like the Gemini Laser. 
Light: Specifically the Light type damage from Light wave energy. This is magic, not mundane light.
Darkness: Darkness damage from Dark energy. Used by demons and such.
Psycho: Psychic energy.
Chi: Focused life-energy dramage. Distinct from Psycho. A hadouken. A Royal Release.
Disenchant: 'Dragon element' - something that is anti-magic.
'''

class ElementalType(models.IntegerField):
        SLASHING = 1
        PIERCING = 2
        ELECTRIC = 3
        EXPLOSIVE = 4
        FIRE = 5
        GRAVITY = 6
        AIR = 7
        ICE = 8
        TOXIC = 9
        BLUNT = 10
        QUAKE = 11
        KARATE = 12
        SONIC = 13
        TIME = 14
        WOOD = 15
        WATER = 16
        PLASMA = 17
        LASER = 18
        LIGHT = 19
        DARKNESS = 20
        PSYCHO = 21
        CHI = 22
        DISENCHANT = 23
        TYPE_CHOICES = (
            (SLASHING, 'Slashing'),
            (PIERCING, 'Piercing'),
            (ELECTRIC, 'Electric'),
            (EXPLOSIVE, 'Explosive'),
            (FIRE, 'Fire'),
            (GRAVITY, 'Gravity'),
            (AIR, 'Air'),
            (ICE, 'Ice'),
            (TOXIC, 'Toxic'),
            (BLUNT, 'Blunt'),
            (QUAKE, 'Quake'),
            (KARATE, 'Karate'),
            (SONIC, 'Sonic'),
            (TIME, 'Time'),
            (WOOD, 'Wood'),
            (WATER, 'Water'),
            (PLASMA, 'Plasma'),
            (LASER, 'Laser'),
            (LIGHT, 'Light'),
            (DARKNESS, 'Darkness'),
            (PSYCHO, 'Psycho'),
            (CHI, 'Chi'),
            (DISENCHANT, 'Disenchant'),
        )

'''
Effects weapons can have. Right now, no weapon can have more than two flags.

Megablast - this ranged attack can be charged up to 3 times.
Exceed - this melee or technique related attack can be charged up to 3 times.
Stable - this attack cannot be charged. What you see is what you get. Buster users
    automatically remove the stable flag from attacks.
Priority - this attack is always the attack that is copied in weapon copy, even if you'd
    rather get some other attack. Top Spin. Bubble Lead.
Blind - The ability to blind your opponent, causing them to take an          
    accuracy debuff their following round. 
Degrade - The ability to disrupt the integrity of your target's armor,       
    causing them to take an armor debuff their following round. Example: Mist   
    Man's Poison Mist. 
Entangle - The ability to tie up your opponent in some fashion for an  
    evasion penalty the following round. Example: Concrete Man's Concrete    
    Shot.  
'''

class WeaponFlag(models.IntegerField):
        MEGABLAST = 1
        EXCEED = 2
        PRIORITY = 3
        STABLE = 4
        BLIND = 5
        DEGRADE = 6
        ENTANGLE = 7
        TYPE_CHOICES = (
            (MEGABLAST, 'Megablast'),
            (EXCEED, 'Exceed'),
            (PRIORITY, 'Priority'),
            (STABLE, 'Stable'),
            (BLIND, 'Blind'),
            (DEGRADE, 'Degrade'),
            (ENTANGLE, 'Entangle')
        )


class Weapon(SharedMemoryModel):
    #weapon obj for copyswap
    db_name = models.CharField('Name', max_length=200)

    db_class = models.IntegerField(
        choices=WeaponClass.TYPE_CHOICES
    )

    db_type_1 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES
    )

    db_type_2 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES, blank=True, null=True
    )

    db_type_3 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES, blank=True, null=True
    )

    db_flag_1 = models.IntegerField(
        choices=WeaponFlag.TYPE_CHOICES, blank=True, null=True
    )

    db_flag_2 = models.IntegerField(
        choices=WeaponFlag.TYPE_CHOICES, blank=True, null=True
    )
    db_date_created = models.DateTimeField('date created', editable=False,
                                            auto_now_add=True, db_index=True)
    
    def __str__(self):
        return self.db_name


class BusterList(SharedMemoryModel):
    '''
    Storing a list of copied attacks as something unique.
    This matches to a character who has 'bustered' these attacks.
    The type as bustered is as buster (ranged) or technique (melee)
    These attacks also contain more metadata such as a timeout.
    Fields 'stable' and 'priority' are removed from these attacks.
    '''

    #weapon obj for copyswap
    db_name = models.CharField('Name', max_length=200)

    db_class = models.IntegerField(
        choices=WeaponClass.TYPE_CHOICES
    )

    db_type_1 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES
    )

    db_type_2 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES, blank=True, null=True
    )

    db_type_3 = models.IntegerField(
        choices=ElementalType.TYPE_CHOICES, blank=True, null=True
    )

    db_flag_1 = models.IntegerField(
        choices=WeaponFlag.TYPE_CHOICES, blank=True, null=True
    )

    db_flag_2 = models.IntegerField(
        choices=WeaponFlag.TYPE_CHOICES, blank=True, null=True
    )

    #additional fields

    db_thief = models.CharField("Stolen By",max_length=100)
    db_date_created = models.DateTimeField('date swiped', editable=False,
                                            auto_now_add=True, db_index=True)
    #todo: autopopulate this. fine for now.
    db_time_out = models.DateTimeField('time out',blank=True, null=True)

    def __str__(self):
        return self.db_name


class GenericAttack(SharedMemoryModel):

    '''
    Generic moves are available to all players.
    They are 'weaponless' and do not have a type.

    Basic Melee, Basic Grapple, Thrown Object
    '''

    db_name = models.CharField('Name', max_length=200)

    db_class = models.IntegerField(
        choices=WeaponClass.TYPE_CHOICES
    )

    def __str__(self):
        return self.db_name