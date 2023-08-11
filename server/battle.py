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
            roll.append(randint(1,10))
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

def check_valid_target(self, char):
    """
    code this check to make sure a target of any assail is:
    in the room with me X
    a valid character X
    that is not KOed
    and is in a showdown with me already
    or unoccupied - remind them to start the showdown.

    """
    caller= self.caller
    
    if not char:
        return False
    if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
        return False
    else:
        return True

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

def process_elements(type_string):
    '''
    process to convert string to structured data to see what element was used
    '''
    val = 0
    
    return val

'''
attack rolls
'''

def roll_attack(attack):
    if attack.db_class == 1:
        return "dex", "aim"
    if attack.db_class == 2:
        return "pow", "force"
    if attack.db_class == 3:
        return "pow", "aim"
    if attack.db_class == 4:
        return "dex", "athletics"
    if attack.db_class == 5:
        return "dex", "force"
    if attack.db_class == 6:
        return "dex", "stealth"
    if attack.db_class == 7:
        return "pow", "athletics"
    if attack.db_class == 8:
        return "aur", "arana"
    if attack.db_class == 9:
        return "aur", "presence"
    if attack.db_class == 10:
        return "cun", "mechanics"
    if attack.db_class == 11:
        return "cun", "computer"
    if attack.db_class == 12:
        return "random", "random"


def process_effects(target, attacker):
    pass

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


