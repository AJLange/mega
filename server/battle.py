"""
Utilities for weapons and armor processing.

Just stubbing these things out.
"""

from datetime import datetime
from world.combat.models import Weapon, WeaponClass, WeaponFlag
from random import randint
from evennia.utils.utils import inherits_from
from django.conf import settings

def do_roll(stat, skill):
    '''
    roll a particular stat-skill combo. Used in combat commands.
    These are pooled rolls so return a list.

    '''

    # pooling stat and skill, but saving old way just in case
    roll_val = stat + skill
    roll = list(range(roll_val))
    for i in range(0,roll_val):
        random = randint(1,10)
        roll[i] = random
    '''
    stat_roll = list(range(stat))
    skill_roll = list(range(skill))
    for i in range(0, stat):
        random = randint(1,10)
        stat_roll[i] = random
    for j in range(0,skill):
        random = randint(1,10)
        skill_roll[j] = random
    return stat_roll, skill_roll
    '''
    return roll

def explode_tens(roll):
    for value in roll:
        if value == 10:
            new_roll = randint(1,10)
            roll.append(new_roll)
            if new_roll == 10:
                explode_tens(new_roll)
    return roll

def roll_to_string(roll):
    die_string = ""
    for value in roll:
        if value == 10:
            die_string = die_string + "|g" + str(value) + "|n "
            continue
        if value >=7:
            die_string = die_string + "|G" + str(value) + "|n "
            continue
        else:
            die_string = die_string + "|R" + str(value)+ "|n "
    return die_string

def listcap_to_string(list):
    if len(list) == 0:
        return "None"
    string = ""
    for i, item in enumerate(list):
        if i < len(list)-1:
            string += (f"{item}, ")
        else:
            string += (f"{item}")
    return string

def check_valid_target(char):
    
    """
    code this check to make sure a target of any possible showdown is:
    in the room with me X
    a valid character X
    """
    
    if not char:
        return False
    if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
        return False
    else:
        return True
    
def check_not_ko(char):
    if (char.db.hp > 0):
        return True
    else:  
        return False
    
def check_morale(char):
    if (char.db.morale > 0):
        return True
    else:
        return False

#check success of a normal roll.

def check_successes(roll):
    successes = 0
    for value in roll:
        if value >= 7:
            successes = successes +1
    return successes

#check success of opposed rolls, including dramatic/crits
#this uses K&T values for now
def check_opposed_rolls(roll1, roll2):
    successes, failures = 0
    crit = False
    drama = False
    for value in roll1:
        if value >= 7:
            successes = successes +1
    for value in roll2:
        if value >= 7:
            failures = failures +1
    if successes >= 5:
        crit = True
    if failures >= 5:
        drama = True

    #process results on a scale of positive or negative

    if successes == failures:
        #this is a tie
        return 0
    if successes > failures and crit:
        return 2
    if successes > failures:
        return 1
    if failures > successes and drama:
        return -2
    if failures > successes:
        return -1


'''
these need to parse lists in the situation where
a list is given
'''


def char_weakness(char):
    weakness = char.db.weakness
    return weakness

def char_resists(char):
    resist = char.db.resist
    return resist

def check_capabilities(char):
    cap = char.db.capabilities
    return cap

def check_weapons(char):
    weapon = char.db.weapons
    return weapon

def process_attack_class(type_string):
    type_string = str(type_string)
    type_string = type_string.upper()

    val = 0
    if type_string == "RANGED":
        val = 1
    elif type_string == "WAVE":
        val = 2
    elif type_string == "THROWN":
        val = 3
    elif type_string == "MELEE":
        val = 4
    elif type_string == "BLITZ":
        val = 5
    elif type_string == "SNEAK":
        val = 6
    elif type_string == "GRAPPLE":
        val = 7
    elif type_string == "SPELL":
        val = 8
    elif type_string == "WILL":
        val = 9
    elif type_string == "GADGET":
        val = 10
    elif type_string == "CHIP":
        val = 11
    elif type_string == "RANDOM":
        val = 12
   
    #nothing found? It will return 0, process as an error
    return val

def get_class_text(num):
    if not num:
        num == 0
    num = int(num)
    element_list = ["None", "Ranged", "Wave" , "Thrown", "Melee", "Blitz", "Sneak,", "Grapple", "Spell","Will", "Gadget", "Chip","Random"]
    return element_list[num]


def process_elements(type_string):
    '''
    process to convert string to structured data to see what element was used
    
    '''
    type_string = str(type_string)    
    type_string = type_string.upper()

    val = 0
    if type_string == "SLASHING":
        val = 1
    elif type_string == "PIERCING":
         val = 2
    elif type_string == "ELECTRIC":
        val = 3
    elif type_string ==  "EXPLOSIVE" :
        val = 4
    elif type_string == "FIRE" :
        val = 5
    elif type_string == "GRAVITY" :
        val = 6
    elif type_string ==  "AIR" :
        val = 7
    elif type_string ==  "ICE" :
        val = 8
    elif type_string ==  "TOXIC" :
        val = 9
    elif type_string ==  "BLUNT" :
        val = 10
    elif type_string ==  "QUAKE" :
        val = 11
    elif type_string ==  "KARATE" :
        val = 12
    elif type_string ==  "SONIC" :
        val = 13
    elif type_string ==  "TIME":
        val = 14
    elif type_string ==  "WOOD" :
        val = 15
    elif type_string ==  "WATER" :
        val = 16
    elif type_string ==  "PLASMA" :
        val = 17
    elif type_string ==  "LASER" :
        val = 18
    elif type_string ==  "LIGHT" :
        val = 19
    elif type_string ==  "DARKNESS" :
        val = 20
    elif type_string ==  "PSYCHO" :
        val = 21
    elif type_string ==  "CHI" :
        val = 22
    elif type_string ==  "DISENCHANT":
        val  = 23
            
    #nothing found? It will return 0, process as an error
    return val

def get_element_text(num):
    if not num:
        num == 0
    num = int(num)
    element_list = ["None", "Slashing", "Piercing", "Electric", "Explosive", "Fire", "Gravity", "Air", "Ice", "Toxic", "Blunt", "Quake", "Karate", "Sonic", "Time", "Wood", "Water", "Plasma", "Laser", "Light", "Darkness", "Psycho", "Chi", "Disenchant"]
    return element_list[num]
 
def get_all_elements(weapon):
    elements_list = []
    elements_list.append(weapon.db_type_1)
    if weapon.db_type_2:
        elements_list.append(weapon.db_type_2)
    if weapon.db_type_3:
        elements_list.append(weapon.db_type_3)
    return elements_list

'''
attack rolls
'''

def roll_attack(char, attack):
    if attack.db_class == 1:
        return char.db.dex, char.db.aim
    if attack.db_class == 2:
        return char.db.pow, char.db.force
    if attack.db_class == 3:
        return char.db.pow, char.db.aim
    if attack.db_class == 4:
        return char.db.dex, char.db.athletics
    if attack.db_class == 5:
        return char.db.dex, char.db.force
    if attack.db_class == 6:
        return char.db.dex, char.db.stealth
    if attack.db_class == 7:
        return char.db.pow, char.db.athletics
    if attack.db_class == 8:
        return char.db.aur, char.db.arcana
    if attack.db_class == 9:
        return char.db.aur, char.db.presence
    if attack.db_class == 10:
        return char.db.cun, char.db.mechanics
    if attack.db_class == 11:
        return char.db.cun, char.db.computer
    if attack.db_class == 12:
        return randint(1,10), randint(1,10)


def process_effects(type_string):
    '''
    process to convert string to structured data to see what element was used
    
    '''
    type_string = str(type_string)    
    type_string = type_string.upper()

    val = 0
    if type_string == "MEGABLAST":
        val = 1
    elif type_string == "EXCEED":
         val = 2
    elif type_string == "PRIORITY":
        val = 3
    elif type_string ==  "STABLE" :
        val = 4
    elif type_string == "BLIND" :
        val = 5
    elif type_string == "DEGRADE" :
        val = 6
    elif type_string == "ENTANGLE" :
        val = 7
    #nothing found? It will return 0, process as an error
    return val

def get_effect_text(num):
    if not num:
        num == 0
    num = int(num)
    element_list = ["None", "Megablast", "Exceed", "Priority", "Stable", "Blind", "Degrade", "Entangle"]
    string_value = str(element_list[num])
    return string_value

def get_all_flags(weapon):
    fx_list = []
    fx_list.append(weapon.db_flag_1)
    if weapon.db_flag_2:
        fx_list.append(weapon.db_flag_2)
    return fx_list


def calc_damage(target,attacker):
    damage = randint(1,10)
    target_defense = target.db.ten
    attacker_dmg_bonus = attacker.db.pow
    damage = damage - target_defense + attacker_dmg_bonus
    return damage

'''
Take in everything to account necessary to see how much damage
an attack does etc.
'''

def process_attack(target, attacker):
    charge_val = attacker.db.chargedice
    if charge_val:
        damage = damage * 2

def copy_attack(target, copier):
    cap_list = copier.check_capabilities()
    copy_type = 0
    for cap in cap_list:
        if cap == "Weapon_copy":
            copy_type = "Buster"
        if cap == "Technique_copy":
            copy_type = "Technique"
    if not copy_type:
        copier.msg("You can't copy a weapon.")
        return 0
    if copy_type == "Buster":
        # copy in the order we want to copy from
        copied_wpn = copier.copy_ranged_weapon(target, copier)
        copier.msg("You copy the weapon %s from the target." % copied_wpn)
        target.msg("%s copies your weapon." % copier.db.name)
        return 0
    if copy_type == "Technique":
        # copy in the order we want to copy from
        copied_wpn = copier.copy_melee_weapon(target, copier)
        copier.msg("You copy the technique %s from the target." % copied_wpn)
        target.msg("%s copies your technique." % copier.db.name)
        return 0


def copy_melee_weapon(target):
    weapon_list = target.check_weapons()
    # by default, copy the primary weapon if no other selection is viable
    copy_this = target.db.primary
    # maybe only a primary has priority but I'll check all just in case
    for weapon in weapon_list:
        if weapon.db_flag_1 == 3 or weapon.db_flag_2 == 3:
            # a weapon has priority, so we're done, copy it
            copy_this = weapon
            return copy_this
        if target.db.primary == weapon:
            if weapon.db_class >= 4 and weapon.db_class <= 7:
                # weapon is fine, copy it
                return copy_this
        if target.db.secondary == weapon:
            if weapon.db_class >= 4 and weapon.db_class <= 7:
                return copy_this
    if not copy_this.db_class >= 4 and copy_this.db_class <=7:
        # never found a suitable weapon, so copy primary as melee
        # todo - be sure effects doesn't process null
        # be sure the effect 'stable' never copies
        # to test, would it make sense to copy 'thrown' as a backup?
        new_weapon = add_weapon_to_db(copy_this.db_name,4,copy_this.db_types,copy_this.db_effects)
        return new_weapon


def copy_ranged_weapon(target, copier):
    weapon_list = target.check_weapons()
    # by default, copy the primary weapon if no other selection is viable
    copy_this = target.db.primary
    # maybe only a primary has priority but I'll check all just in case
    for weapon in weapon_list:
        if weapon.db_flag_1 == 3 or weapon.db_flag_2 == 3:
            # a weapon has priority, so we're done, copy it
            copy_this = weapon
            return copy_this
        if target.db.primary == weapon:
            if weapon.db_class >= 1 and weapon.db_class <= 3:
                # weapon is fine, copy it
                return copy_this
        if target.db.secondary == weapon:
            if weapon.db_class >= 1 and weapon.db_class <= 3:
                return copy_this
    if not copy_this.db_class >= 1 and copy_this.db_class <=3:
        # never found a suitable weapon, so copy primary as ranged
        # to-do - if my aura stat is high enough, can copy spell or will, 
        # otherwise, copy spell or will as ranged
        new_weapon = add_weapon_to_db(copy_this.db_name,1,copy_this.db_types,copy_this.db_effects)
        return new_weapon


def add_weapon_to_db(name,wpn_class,wpn_types,wpn_effects):
    fx_int = 0
    if wpn_effects:
        fx_int = process_effects(wpn_effects)
    if wpn_class.isnumeric():
        #this is already parsed, add it
        type_int = process_elements(wpn_types)
        
        if fx_int:
            weapon = Weapon(name,wpn_class,type_int,None)
        else:
            weapon = Weapon(name,wpn_class,type_int,fx_int)
    return weapon


def num_to_line(val):
    #returns a pretty string that shows the value of a number
       
    string = ""
    l = 0
    color = 1
    bar_length = 10
    string += str(val)
    if val < 10:
        string += "  ["
    elif val == 10:
        string += " ["
    while l < val:
        if l < 5:
            color_string = "00" + str(color + l)
        elif l == 5:
            color_string = "014"
        elif l == 6:
            color_string = "015"
        elif l <= 8:
            color_string = "024"
        else:
            color_string = "035"
        
        string += (f"|[{color_string}|{color_string}...")
        l = l + 1
        bar_length = bar_length -1
    if bar_length <= 0:
        string += "|n]"
        return string
    while bar_length:        
        bar_length = bar_length -1
        string += "|n:::"           
   
    string += "|n]"
    return string


def num_to_skill(val):
    #returns a pretty string that shows the value of a number,
    # but in green.
       
    string = ""
    l = 0
    color = 40
    bar_length = 5
    string += str(val)
    string += " ["

    while l < val:
        if l <= 4:
            color_string = "0" + str(color + l)
        else:
            color_string = "050"
        
        string += (f"|[{color_string}|{color_string}...")
        l = l + 1
        bar_length = bar_length -1
    if bar_length <= 0:
        string += "|n]"
        return string
    while bar_length:        
        bar_length = bar_length -1
        string += "|n:::"           
   
    string += "|n]"
    return string