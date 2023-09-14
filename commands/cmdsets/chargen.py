"""
Commands related to character creation.
For now lock these commands only to staff
and only in certain rooms flagged for chargen.

Later may add a monster-maker or something for
player GMs to use.
"""

from django.conf import settings
from evennia import CmdSet
from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.rooms import ChargenRoom
from evennia import create_object
from evennia.utils.utils import inherits_from
from evennia.objects.models import ObjectDB
from typeclasses.accounts import Account
from world.combat.models import Weapon
from world.armor.models import ArmorMode, Capability
from server.battle import process_elements, process_attack_class, process_effects


'''
What characters must have:

Fixed set by staff:
Name
Function
Quote
Profile 
Gender
Game (if applicable)
Type (FC or OC)
Template (eg Race, can have multiple)
Specialties (the cute list of skills)
Focuses (the skill specialties to be rolled)

Primary Weapon

Combat and systems:

Set Per armor form.

Stats
Skills
Abilities 
AttackTypes
Weakness
Resist
Height 
Speed

Faction related info (to be added later)

Flags which are flexible per scene:
HP
Morale

OOCfinger info:
Can be set by player so not in this file
Email
Discord
Alias
Alts
Timezone
Voice
Info

'''




class CmdStartChargen(MuxCommand):
    """
    
    +chargen

    This command will temporarily give you access to the rest
    of the chargen commands. It can only be done in a chargen
    enabled room.  For now, this command is only available
    to staffers in staff only areas.

    To do chargen in order:
    +chargen
    +createpc <name>
    +workchar <name>
    +setstat/<namestat> <1-10> (for all 7 stats)
    +setskill/<nameskill> <1-5> (for all 12 skills)
    +setprofile/<attribute> <value> (for all 7 text attributes)
    +setweapon <name> (for all weapons, including /primary and /secondary)
    +settemplate <name> (for the character's templates (not structured data))
    +setcapability <name> (for each capability to add)
    +setfocuses <name> (as many times as needed for all focuses)

    If there are armor modes, create them by doing
    +setarmor <name> = type>

    +finishchargen when done.

    +player <character> = <player>
    to assign this character to a player account.

    Armor modes, and characters with multiple power sets, are not working
    in the pre-alpha build.

    Please note that if the database is reset, your working character is not
    reset, but you will lose access to +chargen commands.

    """
    
    key = "+chargen"
    help_category = "Character"
    locks = "perm(Builder)"

    def func(self):
        caller = self.caller
        location = caller.location
        chargeninit = "You have begun character creation. You now have access to character setup commands. When you are done making a character, +finishchargen to make sure you didn't miss anything. For the list of commands, see +help +chargen."
        
        if isinstance(location, ChargenRoom):
            
            caller.msg(chargeninit)
                # add the chargen command set
            caller.cmdset.add(ChargenCmdset, persistent=True)
            
        else:
            caller.msg("You cannot do chargen here.")
            return
        


'''
CreateWeapon partially functions.
Ways this is broken:
    Not processing the extra fields properly
    Not checking for duplicates (do not make the same weapon twice, 
        but will put a failsafe check in setweapon.)
'''

class CmdCreateWeapon(MuxCommand):
    """
    Create a new weapon.

    Usage:
        +addweapon <name>=<class> <type>
        +addweapon <name>=<class> <type> <type> <type>
        +addweapon <name>=<class> <type>, <effect>
        eg.
        +addweapon Gemini Laser=Ranged Laser
        +addweapon Magnet Missle=Ranged Gravity Blunt
        +addweapon Top Spin=Blitz Karate, Priority


    This adds a new weapon to the database of weapons.
    A simple version creates a weapon with a single type.
    A weapon can have up to three types. Seperate by spaces.

    A weapon can also have up to two effects, but this will
    not be common. Space effects out with commas, then spaces.

    Weapons currently accept the following classes:
    Ranged, Wave, Thrown, Melee, Blitz, Sneak
    Grapple, Spell, Will, Gadget, Chip, Random

    Types:
    Slashing, Piercing, Electric, Explosive, Fire, Gravity
    Air, Ice, Toxic, Blunt, Quake, Karate, Sonic, Time, Wood
    Water, Plasma, Laser, Light, Darkness, Psycho, Chi, Disenchant
    
    Effects:
    Megablast, Exceed, Stable, Priority, Blind, Degrade, Entangle
    """

    key = "addweapon"
    aliases = ["+addweapon"]
    locks = "perm(Builder)"
    help_category = "Character"

    def func(self):        
        caller = self.caller
        args = self.args
        errmsg = "Add what weapon? See help addweapon."
        if not args:
            caller.msg(errmsg)
            return

        weapon_name = self.lhs
        weapon_stats = self.rhs
        if not weapon_stats:
            caller.msg(errmsg)
            return

        #does the weapon have effects?
        divide_fx = weapon_stats.split(", ")
        # todo, error check for extra spaces
        effects_list = 0
        if len(divide_fx) > 1:
            effects = divide_fx.pop(1)
            effects_list = effects.split(" ")
        
        #do the rest
        types_list = divide_fx[0].split(" ")
        weapon_class = types_list[0]
        types_list.pop(0)
        element_list =[]

        #convert weapon class to DB stored integer
        style_weapon = process_attack_class(weapon_class)
        if style_weapon == 0:
            caller.msg("Invalid weapon class. No weapon added.")
            return 
        for element in types_list:
            element = process_elements(element)
            if element == 0:
                caller.msg("Invalid element choice. No weapon added.")
                return 
            element_list.append(element)
        
        # TODO - effect flags are not in, do not do anything with these yet

        # preventing out of range errors if no more elements
        errmsg = "Sorry, an error occured."
        if effects_list:
            if len(element_list) == 1:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0], db_flag_1=1)
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s Effects %s" % (weapon_name, weapon_class, types_list, effects_list) )
                    return
                else: 
                    caller.msg(errmsg)
                    return
            elif len(element_list) ==2:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0], db_type_2= element_list[1], db_flag_1=1)
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s Effects %s" % (weapon_name, weapon_class, types_list, effects_list) )
                    return
                else: 
                    caller.msg(errmsg)
                    return
            elif len(element_list) == 3:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0], db_type_2= element_list[1], db_type_3= element_list[2], db_flag_1=1)
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s Effects %s" % (weapon_name, weapon_class, types_list, effects_list) )
                    return
                else: 
                    caller.msg("Sorry, an error occured.")
            elif len(element_list) > 3:
                caller.msg("Too many elements for that weapon.")
                return
            else:
                caller.msg(errmsg)
                return
        else:
            if len(element_list) == 1:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0])
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s " % (weapon_name, weapon_class, types_list) )
                    return
                else: 
                    caller.msg(errmsg)
                    return
            elif len(element_list) ==2:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0], db_type_2= element_list[1])
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s" % (weapon_name, weapon_class, types_list) )
                    return
                else: 
                    caller.msg(errmsg)
                    return
            elif len(element_list) == 3:
                new_weapon = Weapon.objects.create(db_name=weapon_name, db_class=style_weapon, db_type_1=element_list[0], db_type_2= element_list[1], db_type_3= element_list[2])
                if new_weapon:
                    caller.msg("Added weapon |w%s|n: Class %s Types %s " % (weapon_name, weapon_class, types_list) )
                    return
                else: 
                    caller.msg("Sorry, an error occured.")
            elif len(element_list) > 3:
                caller.msg("Too many elements for that weapon.")
                return
            else:
                caller.msg(errmsg)
                return


class CmdCreateCapability(MuxCommand):
    """
    Create a new capability, adding this to the selectable
    db of Capabilities. 

    Usage:
        +addcapabilty <name>
        +addcapabilty Enhanced-Senses

    This adds a new capability to the database of capabilities.

    This DB is actually called Capabilitys, because Django, but 
    don't worry about it.
    
    Capabilities interact with the combat and non combat code in 
    various ways when a string is matched. This command should be 
    used rarely, because it is the database add. It is only used 
    the first time a capability is added to the DB, not during 
    general chargen.

    To actually set a capability on a character from the existing
    database, use +setcapability instead.

    """

    key = "addcapability"
    aliases = ["+addcapability"]
    locks = "perm(Builder)"
    help_category = "Character"

    def func(self):        
        caller = self.caller
        args = self.args
        errmsg = "Add what capabilty? See help addcapabilty."
        if not args:
            caller.msg(errmsg)
            return

        cap_name = self.args
        
        new_cap = Capability.objects.create(db_name=cap_name)
        if new_cap:
            caller.msg("Added capability |w%s|n to the Capability database." % cap_name )
        else:
            caller.msg("Sorry, an error occured.")
        

class CmdCreatePC(Command):
    """
    Create a new PC

    Usage:
        +createPC <name>

    Creates a new, named PC. 
    """
    key = "createpc"
    aliases = ["+createPC"]
    locks = "perm(Builder)"
    help_category = "Character"
    
    def func(self):
        "creates the object and names it"
        caller = self.caller
        if not self.args:
            caller.msg("Usage: +createPC <name>")
            return

        # set name as set
        name = self.args.lstrip()
        # create in caller's location
        typeclass = settings.BASE_CHARACTER_TYPECLASS
        start_location = caller.location
        default_home = ObjectDB.objects.get_id(settings.DEFAULT_HOME)
        permissions = settings.PERMISSION_ACCOUNT_DEFAULT
        character = create_object(typeclass,
                      key=name,
                      location=caller.location, home=default_home, permissions=permissions,
                      locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)

            
        # announce
        message = "%s created the PC '%s'."
        caller.msg(message % ("You", name))
        caller.location.msg_contents(message % (caller.key, name),
                                                exclude=caller)
        return 


class CmdWorkChar(Command):
    """
    Work on a Character. This sets the character that you 
    are working on. To be used after creating the PC using +createpc.

    Usage:
        +workchar <name>

    Sets the character to work on. Only works in the chargen room.
    Is persisent on server reset, just in case you get interrupted.

    """
    key = "+workchar"
    aliases = ["workchar"]
    help_category = "Character"
    locks = "perm(Builder)"
    
    def func(self):
        "creates the object and names it"
        caller = self.caller
        if not self.args:
            caller.msg("Usage: +workchar <name>")
            return

        # set name as set
        name = self.args.lstrip()
        

        #character = ObjectDB.objects.filter(db_key__iexact=name)[0]
        character = self.caller.search(name, global_search=True)
        if not character:
            caller.msg("Sorry, couldn't find that PC.")
            return
        if not inherits_from(character, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Sorry, couldn't find that PC.")
            return    
        
        # announce
        caller.db.workingchar = character
        
        message = "%s now working on the PC '%s'."
        caller.msg(message % ("You're", name))
        caller.location.msg_contents(message % (caller.key, name),
                                                exclude=caller)
        return 

class CmdSetPlayer(MuxCommand):
    '''
    Give a character to a player.

    Usage:
        +player <character>=<account>

    This will assign the character you specify to the account you specify.

    To remove a character from an account, use +unplayer.
    '''

    key = "player"
    help_category = "Character"
    locks = "perm(Builder)"
    aliases = ["+player", "+setplayer", "setplayer"]

    def func(self):
        "This performs the actual command"

        if not self.args:
            self.msg("Usage: player <charname> = <account>")
            return
        char = self.lhs
        account = self.rhs

        '''
        Make sure there is a character by this name
        Make sure there is an account by this name
        '''
        if not ObjectDB.objects.filter(db_typeclass_path=settings.BASE_CHARACTER_TYPECLASS, db_key__iexact=char):
            
            self.msg("|rA character named '|w%s|r' wasn't found.|n" % char)
            return
        else:
            this_char = ObjectDB.objects.filter(db_key__iexact=char)[0]

        if not Account.objects.filter(db_typeclass_path=settings.BASE_ACCOUNT_TYPECLASS, username__iexact=account):
            
            self.msg("|rAn account named '|w%s|r' wasn't found.|n" % account)
            return
        else:
            this_account = Account.objects.filter(username__iexact=account)[0]
        
        '''        
        We found it, so give the account permissions to puppet the character.
        '''
        this_char.locks.add(
            "puppet:id(%i) or pid(%i) or perm(Developer) or pperm(Developer);delete:id(%i) or perm(Admin)"
            % (this_char.id, this_account.id, this_account.id)
        )
        this_account.db._playable_characters.append(this_char)
        self.msg("|rAssigned character '|w%s|r' to player '|w%s|r'|n" % (char,account))

        return 


class CmdUnPlayer(MuxCommand):
    '''
    Take a character away from a player.

    Usage:
        +unplayer <character>=<account>

    This will remove a character from a particular account.

    To add a character to an account, use +player.
    '''

    key = "unplayer"
    help_category = "Character"
    locks = "perm(Builder)"
    aliases = ["+unplayer"]


    def func(self):
        "This performs the actual command"
        if not self.args:
            self.msg("Usage: player <charname> = <account>")
            return
        char = self.lhs
        account = self.rhs

        '''
        Make sure there is a character by this name
        Make sure there is an account by this name
        '''
        if not ObjectDB.objects.filter(db_typeclass_path=settings.BASE_CHARACTER_TYPECLASS, db_key__iexact=char):
            
            self.msg("|rA character named '|w%s|r' wasn't found.|n" % char)
            return
        else:
            this_char = ObjectDB.objects.filter(db_key__iexact=char)[0]

        if not Account.objects.filter(db_typeclass_path=settings.BASE_ACCOUNT_TYPECLASS, username__iexact=account):
            
            self.msg("|rAn account named '|w%s|r' wasn't found.|n" % account)
            return
        else:
            this_account = Account.objects.filter(username__iexact=account)[0]
        
        '''        
        We found it. Was this person actually playing this character? if so, remove.
        '''
        if this_account.db._playable_characters.count(this_char):
            this_char.locks.remove(
            "puppet:id(%i) or pid(%i) or perm(Developer) or pperm(Developer);delete:id(%i) or perm(Admin)"
            % (this_char.id, this_account.id, this_account.id)
        )
            this_account.db._playable_characters.remove(this_char)
            this_account.db._last_puppet = 0
            self.msg("|rRemoved character '|w%s|r' from player '|w%s|r'|n" % (char,account))
        else:
            self.msg("|rDidn't find '|w%s|r' in '|w%s|r''s account.|n" % (char,account))

        return 



class CmdSetStat(MuxCommand):
    """
    Sets the stats on a character. 
    Staff creating characters only.

    Usage:
      +setstat/power <1-10>
      +setstat/<namestat> <1-10> 


    Stats in this system are 
    Power, Dexterity, Tenacity
    Cunning, Education, Charisma, Aura

    """
    
    key = "setstat"
    help_category = "Character"
    locks = "perm(Builder)"
    alias = "+setstat"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar 
        if not character:
            caller.msg("You aren't working on an active character.")
            return
        errmsg = "You must supply a number between 1 and 10."
        if not self.switches:
            caller.msg("Set which stat?")
            return
        if not self.args:
            caller.msg(errmsg)
            return
        try:
            stat = int(self.args)
        except ValueError:
            caller.msg(errmsg)
            return
        if not (1 <= stat <= 10):
            caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        if "power" in self.switches:
            character.db.pow = stat
        if "dexterity" in self.switches:
            character.db.dex = stat
        if "tenacity" in self.switches:
            character.db.ten = stat
        if "cunning" in self.switches:
            character.db.cun = stat
        if "education" in self.switches:
            character.db.edu = stat
        if "charisma" in self.switches:
            character.db.chr = stat
        if "aura" in self.switches:
            character.db.aur = stat

        caller.msg(f"The PC's {self.switches} was set to %i." % stat)



class CmdSetSkills(MuxCommand):
    """
    Sets the skills on a character. 
    Staff creating characters only.

    Usage:
      +setskill/Discern <1-5>
      +setskill/<nameskill> <1-5> 


    Valid skills in this version are
    Discern
    Athletics
    Aim
    Force
    Mechanics
    Medicine
    Computer
    Stealth
    Heist
    Convince
    Presence
    Arcana


    """
    
    key = "setskill"
    help_category = "Character"
    locks = "perm(Builder)"
    alias = "+setskill"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar 
        if not character:
            caller.msg("You aren't working on an active character.")
            return
        errmsg = "You must supply a number between 1 and 10."
        if not self.switches:
            caller.msg("Set which skill?")
            return
        if not self.args:
            caller.msg(errmsg)
            return
        try:
            stat = int(self.args)
        except ValueError:
            caller.msg(errmsg)
            return
        if not (1 <= stat <= 10):
            caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        if "discern" in self.switches:
            character.db.discern = stat
        if "aim" in self.switches:
            character.db.aim = stat
        if "athletics" in self.switches:
            character.db.althetics = stat
        if "force" in self.switches:
            character.db.force = stat
        if "mechanics" in self.switches:
            character.db.mechanics = stat
        if "medicine" in self.switches:
            character.db.medicine = stat
        if "computer" in self.switches:
            character.db.computer = stat
        if "stealth" in self.switches:
            character.db.stealth = stat
        if "heist" in self.switches:
            character.db.heist = stat
        if "convince" in self.switches:
            character.db.convince = stat
        if "presence" in self.switches:
            character.db.presence = stat
        if "arcana" in self.switches:
            character.db.arcana = stat
        caller.msg(f"The PC's {self.switches} was set to %i." % stat)



class CmdSetProfileAttr(MuxCommand):
    """
    Sets the profile info of a character.
    Staff creating characters only.

     This command sets the +finger attributes and a few other 
     static attributes. The full list is as follows: Type, 
     Game, Function, Quote, Profile, Gender, Specialties
     (formerly skills)

    For now just put all the skills in one list.

    Usage:
      +setprofile/<attribute> <value>

    """
    
    key = "setprofile"
    help_category = "Character"
    locks = "perm(Builder)"
    alias = "+setprofile]"

    '''
    This works, but it's pretty sloppy and could really use a refactor.
    '''

    def func(self):
        "This performs the actual command"
        errmsg = "Set value to what?"
        caller = self.caller
        character = caller.db.workingchar 
        if not character:
            caller.msg("You aren't working on an active character.")
            return
        if "gender" in self.switches or "Gender" in self.switches:
            if self.args:
                text = self.args
                character.db.gender = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "type" in self.switches or "Type" in self.switches:
            if self.args:
                text = self.args
                character.db.type = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "quote" in self.switches or "Quote" in self.switches:
            if self.args:
                text = self.args
                character.db.quote = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "profile" in self.switches or "Profile" in self.switches:
            if self.args:
                text = self.args
                character.db.profile = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "game" in self.switches or "Game" in self.switches:
            if self.args:
                text = self.args
                character.db.game = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "function" in self.switches or "Function" in self.switches:
            if self.args:
                text = self.args
                character.db.function = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return
        if "specialties" in self.switches or "Specialties" in self.switches:
            if self.args:
                text = self.args
                character.db.specialties = self.args
                caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)
            else:
                caller.msg(errmsg)
            return 
        if not self.args:
            self.caller.msg("Not a valid attribute.")
            return
        else:
            self.caller.msg("Not a valid attribute.")
            return

'''
        try:
            text = self.args
        except ValueError:
            self.caller.msg("Not a valid attribute.")
            return
'''
        


class CmdSetAttribute(MuxCommand):
    """
    Sets the assorted info on a character which is 
    different per armor form.

     The full list is as follows:  
     Weakness, Resistance, Height, Speed

    For now just put all the skills in one list.

    Usage:
      +setattribute/<attribute> <value>

    """
    
    key = "+setattribute"
    help_category = "Character"
    locks = "perm(Builder)"
    

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar
        if not character:
            caller.msg("You aren't working on an active character.")
            return

        errmsg = "Not a valid attribute."
        if "weakness" in self.switches:
            if self.args:
                character.db.weakness = process_elements(self.args)
            else:
                caller.msg(errmsg)
            if character.db.weakness == 0:
                caller.msg("Value not set, please be sure this is spelled correctly.")
                caller.msg("Weakness type set to 'None'.")
            return
        if "resistance" in self.switches:
            if self.args:
                character.db.resistance = process_elements(self.args)
            else:
                caller.msg(errmsg)
            if character.db.weakness == 0:
                caller.msg("Value not set, please be sure this is spelled correctly.")
                caller.msg("Resist type set to 'None'.")
            return
        if "height" in self.switches:
            if self.args:
                character.db.height = self.args
            return
        if "speed" in self.switches:
            if self.args:
                character.db.speed = self.args
        if "strength" in self.switches:
            if self.args:
                character.db.strength = self.args
            return
        
        if not self.args:
            caller.msg(errmsg)
            return
        try:
            text = self.args
        except ValueError:
            caller.msg(errmsg)
            return

        caller.msg(f"Profile Attribute {self.switches} was set to: %s" % text)


'''

Not working for now. Just copy+paste an entire list.

class CmdSetSpecialty(Command):
    """
    Sets the profile info of a character.
    This is for setting the specialties of characters, 
    formerly known as skills. Just a fun thing to do. Should accept
    a value or list of values spaced out by commas.

    Usage:
      +setspecialty <specialty>
      +setspecialty <spec>, <another spec>

    """
    
    key = "+setspecialty"
    help_category = "Chargen"

    def func(self):
        "This performs the actual command"
        errmsg = "What text?"
        self.caller.db.quote = text
        self.caller.msg("Added a specialty at: %s" % text)
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            text = self.args
        except ValueError:
            self.caller.msg(errmsg)
            return
        
'''

# to do above, make it a proper list you can add to

class CmdSetWeapons(MuxCommand):
    """
    Adding weapons to characters.

    Usage:
      +setweapon <name>
      +setweapon/primary <name>
      +setweapon/secondary <name>

    This sets the weapon specified on the working character,
    on the working armor mode. Use /primary or /secondary
    to set the primary and secondary weapons, which show up
    on the character sheet and have priority for weapon copy
    attacks.

    Weapons need to be added to the weapon database first with
    +addweapon.

    """
    

    key = "setweapon"
    help_category = "Character"
    locks = "perm(Builder)"
    aliases = ["+setweapon"]

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar
        switches = self.switches

        if not character:
            caller.msg("You aren't working on an active character.")
            return

        errmsg = "What weapon?"
        if not self.args:
            caller.msg(errmsg)
            return
        
        if switches:
            if not "primary" in switches and not "secondary" in switches:
                caller.msg("Invalid switch.")
                return        
        
        text = self.args
        
        check_weapon = Weapon.objects.filter(db_name__iexact=text)
        if not check_weapon:
            caller.msg("That weapon was not found. Add it first using +addweapon.")
            return
        if len(check_weapon) > 1:
            caller.msg("Error, duplicate weapons found. Please fix this in database.")
            return

        weapon = Weapon.objects.filter(db_name__iexact=text)[0]

        try:
            
            character.db.weapons.append(weapon)
            
            if switches:
                if "primary" in switches:
                    character.db.primary = weapon
                    caller.msg("Added the weapon (as primary): %s" % text)
                    return
                if "secondary" in switches:
                    character.db.secondary = weapon
                    caller.msg("Added the weapon (as secondary): %s" % text)
                    return
            caller.msg("Added the weapon: %s" % text)
            return
        except ValueError:
            caller.msg(errmsg)
            return
        

class CmdSetTemplate(Command):
    """
    Setting the templates for a character.

    Usage:
      +settemplate <name>
      +settemplate Human
      +settemplate Cyborg, Adept

    This sets the templates for characters. This simply takes a string 
    as data and has no actual impact on the combat system for the time
    being. A comma-seperated list is valid input.

    You can also use +setprofile/type <template>


    """
    
    key = "settemplate"
    help_category = "Character"
    aliases = ["+settemplate"]

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar 

        if not character:
            caller.msg("You aren't working on an active character.")
            return
        errmsg = "What text?"
        if not self.args:
            caller.msg(errmsg)
            return
        try:
            text = self.args
            character.db.type = text
            caller.msg("Added the template: %s" % text)
        except ValueError:
            caller.msg(errmsg)
            return
        
class CmdSetFocus(Command):
    """
    Setting the templates for a character.

    Usage:
      +setfocus <name>
      +setfocus Meditation

    This adds a focus to a character. 
    
    A character can only have 5 focuses. Focuses are free text to write
    anything within reason. When using that focus in a non-showdown situation,
    the character can get 2 extra dice.


    """
    
    key = "setfocus"
    help_category = "Character"
    aliases = ["+setfocus"]

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar 

        if not character:
            caller.msg("You aren't working on an active character.")
            return
        errmsg = "What text?"
        if not self.args:
            caller.msg(errmsg)
            return
        
        get_focuses = character.db.focuses
        if len(get_focuses) >= 5:
            caller.msg("That character already has 5 focuses. Remove a focus with +removefocus")
        try:
            text = self.args
            character.db.workingchar.append(text)
            caller.msg("Added the focus: %s" % text)
        except ValueError:
            caller.msg(errmsg)
            return


class CmdRmFocus(Command):
    """
    Setting the templates for a character.

    Usage:
      +removefocus <name>

    This removes a focus from a character so that a new one might be added.
    

    """
    
    key = "removefocus"
    help_category = "Character"
    aliases = ["+removefocus"]

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar
        args = self.args

        if not character:
            caller.msg("You aren't working on an active character.")
            return
        errmsg = "What text?"
        if not self.args:
            caller.msg(errmsg)
            return
        
        get_focuses = character.db.focuses

        for focus in get_focuses:
            if focus == args:
                get_focuses.pop(focus)
                caller.msg("Removed the focus: %s" % focus)
                return
        caller.msg("That focus wasn't found. Exact matches only.")
        return


class CmdSetCapability(MuxCommand):
    """
    Setting the capabilities on a character.

    Usage:
      +setcapability <name>
      +setcapabilty Flight
      +setcap Flight 

    This adds a capability to the working character. Capabilities
    must be valid capabilities that are in the Capability database.

    Since 'capability' is a long word, 'setcap' can be used for sure.
    
    To add a new capability to the database, use +addcapability.
    This should not be used often.

    """
    
    key = "setcapability"
    help_category = "Character"
    aliases = ["+setcapability", "setcap", "+setcap"]

    def func(self):
        "This performs the actual command"
        caller = self.caller
        character = caller.db.workingchar 

        if not character:
            caller.msg("You aren't working on an active character.")
            return
        if not self.args:
            caller.msg("What text?")
            return
        try:
            text = self.args
            #make sure this is valid
            valid_cap = Capability.objects.filter(db_name__iexact=text)
            if not valid_cap:
                caller.msg("Not a valid capability. See +addcapability.")
                return
            this_cap = Capability.objects.filter(db_name__iexact=text)[0]
            
            character.db.capabilities.append(this_cap)
            caller.msg(f"Added the capability {text} to character {character}.")
        except ValueError:
            caller.msg("An error occured.")
            return
        


class CmdSetArmor(MuxCommand):
    """
    Sets the current stats on a character to an armor mode.

    Usage:
      +setarmor <name of armor>=<armor type>
      +setarmor Mega Man=1

    Armors are set as an INTEGER as below due to data structure.

    Valid armor types are Mode, Stance, Focus, Form
    VR, Summon, Minion, System, and just Armor.

    1 - Mode - Technological mode change. Typical for robots.
    2 - Stance - if this is a change in fighting style.
    3 - Focus - the fight gets serious now, so I doubled down.
    4 - Form - Mutated into another form or changed bodies.
    5 - VR - Jacking in to a virtual form.
    6 - Summon - Summoning a pet or assist.
    7 - Minion - Playing as another character or squad.
    8 - System - Using a special system activation, such as Double Gear.
    9 - Armor - When you're not sure which one to use.

    """
    
    key = "setarmor"
    help_category = "Character"
    locks = "perm(Builder)"
    alias = "+setarmor"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        char = caller.db.workingchar 

        if not char:
            caller.msg("You aren't working on an active character.")
            return

        errmsg = "Syntax error. See help +setarmor."
        args = self.args
        if not self.args:
            caller.msg(errmsg)
            return
        armor_type = self.rhs
        name = self.lhs

        if not armor_type:
            caller.msg(errmsg)
            return
        
        try:
            armor_type = int(armor_type)
        except ValueError:
            caller.msg(errmsg)
            return
        if not (1 <= armor_type <= 9):
            caller.msg(errmsg)
            return
        
        if not char.db.primary or not char.db.secondary:
            caller.msg("Character missing necessary attributes. Did you set primary weapons?")
            return
        
        new_armor = ArmorMode.objects.create(db_name=name, db_swap = armor_type, db_pow = char.db.pow, db_dex = char.db.dex, db_ten = char.db.ten, db_cun = char.db.cun, 
                                            db_edu = char.db.edu, db_chr = char.db.chr, db_aur = char.db.aur, db_size = char.db.size, db_speed = char.db.speed, db_strength = char.db.strength,
                                            db_resistance = char.db.resistance, db_weakness = char.db.weakness,
                                            db_discern = char.db.discern, db_aim = char.db.aim, db_athletics = char.db.athletics,
                                            db_force = char.db.force, db_mechanics = char.db.mechanics, db_medicine = char.db.medicine, db_computer = char.db.computer,
                                            db_stealth = char.db.stealth, db_heist = char.db.heist, db_convince = char.db.convince, db_presence = char.db.presence, db_arcana = char.db.arcana,
                                            db_primary = char.db.primary, db_secondary = char.db.secondary
                                            )
        #db_capabilities.set(char.db.capabilities), db_weapons.set(char.db.weapons)
        try:
            char.db.armor.append(new_armor)
            caller.msg("Added an armor named: %s" % name)
        except:
            caller.msg("Sorry, some error occured.")
        
        
        

class CmdFinishChargen(MuxCommand):
    """
    This command makes sure the character you are working on
    is complete.

    Usage:
      +finishchargen

    This will return errors if any attributes are missing from the
    character that you are working on.

    """
    
    key = "+finishchargen"
    help_category = "Character"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        char = caller.db.workingchar
        if not char:
            self.caller.cmdset.remove(ChargenCmdset)
            caller.msg("You weren't working on a character.")
            return
        errmsg = "Some error occured."
        if not char.db.weakness:
            caller.msg("Missing attribute: weakness\n")
        if not char.db.resistance:
            caller.msg("Missing attribute: resistance\n")
        if not char.db.height:
            caller.msg("Missing attribute: height\n")
        if not char.db.speed:
            caller.msg("Missing attribute: speed\n")
        if not char.db.strength:
            caller.msg("Missing attribute: strength\n")
        if not char.db.gender:
            caller.msg("Missing attribute: gender\n")
        if not char.db.type:
            caller.msg("Missing attribute: type\n")
        if not char.db.quote:
            caller.msg("Missing attribute: quote\n")
        if not char.db.profile:
            caller.msg("Missing attribute: profile\n")
        if not char.db.game:
            caller.msg("Missing attribute: game\n")
        if not char.db.function:
            caller.msg("Missing attribute: function\n")
        if not char.db.specialties:
            caller.msg("Missing attribute: specialties\n")

        try:
            self.caller.cmdset.remove(ChargenCmdset)
            caller.msg("Char Creation Done. Make sure your character has stats and abilities set.")
        except ValueError:
            caller.msg(errmsg)
            return


class ChargenCmdset(CmdSet):
    """
    This cmdset is used in character generation areas.
    """
    key = "Chargen"
    def at_cmdset_creation(self):
        "This is called at initialization"
        self.add(CmdCreatePC())
        self.add(CmdSetStat())
        self.add(CmdWorkChar())
        #self.add(CmdSetSpecialty())
        self.add(CmdSetSkills())
        self.add(CmdCreateWeapon())
        self.add(CmdSetWeapons())
        self.add(CmdSetArmor())
        self.add(CmdSetProfileAttr())
        self.add(CmdSetTemplate())
        self.add(CmdFinishChargen())
        self.add(CmdSetPlayer())
        self.add(CmdUnPlayer())
        self.add(CmdCreateCapability())
        self.add(CmdSetCapability())
