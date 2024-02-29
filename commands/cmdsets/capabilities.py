
from evennia import CmdSet
from commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi
from random import randint
from evennia import Command, InterruptCommand
from server.battle import roll_attack, check_valid_target, explode_tens, roll_to_string, check_successes, check_capabilities, copy_attack, do_roll, check_morale, check_not_ko
from evennia.utils.utils import inherits_from
from django.conf import settings
from world.combat.models import Weapon
from world.armor.models import ArmorMode, Capability

'''
Capabilities. Some are combat related and some are not.
'''


class CmdWeaponCopy(MuxCommand):
    """
    Copy the weapon of your target.

    Usage:
      wcopy <target>

    If you have a weapon copy ability, this copies the weapon of the target.
    What weapon you copy depends on if you copy primarily ranged, or primarily melee weapons.
    This will be on your sheet as either Buster-Copy or Technique-Copy.

    Copied weapons will be listed on your weapon sheet automatically.

    """
    
    key = "wcopy"
    aliases = ["+wcopy", "buster","+buster"]
    help_category = "Dice"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg("Initiating weapon copy.")
        if not args:
            caller.msg("Copy whose weapon?")
            return
        
        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return
        
        try:
            
            char = caller.search(char, global_search=False)
            if not char:
                caller.msg("No target.")
                return
            if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                caller.msg("No target.")
                return

            #process attack copy code
            new_weapon = copy_attack(char,caller)


        except ValueError:
            caller.msg(errmsg)
            return
        


class CmdEmulate(MuxCommand):
    """
    Copy the armor and form of your target.

    Usage:
      emulate <target>

    If you have the Emulate ability, this will capture a copy of your opponent's current
    armor and transfer it to you. The copy is not idenitical to the other person's
    as only certain stats are copied to your version:

    The following stats are calculated into the emulated armor:

    Stats: Power, Dexterity, Tenacity
    Weapons: Primary and Secondary
    Size, Speed, Strength, Resistance, Weakness
    Abilities: Aim, Athletics, Force, Stealth, Presence
    Capabilities: Certain Capabilties are copied (such as Flight)


    Copied armor forms are limited to 4 armor forms. They will time out after
    a month of real life time from the time you copied the armor.

    Copied weapons will be listed on your weapon sheet automatically.

    """
    
    key = "emulate"
    aliases = ["+emulate"]
    help_category = "Powers"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg("Initiating weapon copy.")
        if not args:
            caller.msg("Copy whose weapon?")
            return
        
        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return
        
        try:
            
            char = caller.search(char, global_search=False)
            if not char:
                caller.msg("No target.")
                return
            if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                caller.msg("No target.")
                return

            #process attack copy code
            new_weapon = copy_attack(char,caller)


        except ValueError:
            caller.msg(errmsg)
            return
        

class CmdCrossfuse(MuxCommand):
    """
    Copy some of the abilities of another character onto yourself.

    Usage:
      Crossfuse <target>

    If you have the Crossfuse ability, this will capture a modified version
    of your opponent's current armor and transfer to you. This 
    version of the armor isn't identical to the stats of your opponent
    but is partially identical, taking a weighted average between the target's stats
    and yours. 

    Stats: Power, Dexterity, Tenacity
    Weapons: Primary and Secondary
    Size, Speed, Strength, Resistance, Weakness
    Abilities: Aim, Athletics, Force, Stealth, Presence
    Capabilities: Certain Capabilties are copied (such as Flight)

    Copied armor forms are limited to 4 armor forms. They will time out after
    a month of real life time from the time you copied the armor.

    This command does not work yet and is just stubbed out!

    """
    
    key = "mimic"
    aliases = ["+mimic"]
    help_category = "Powers"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg("Initiating weapon copy.")
        if not args:
            caller.msg("Copy whose weapon?")
            return
        
        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return
        
        try:
            
            char = caller.search(char, global_search=False)
            if not char:
                caller.msg("No target.")
                return
            if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                caller.msg("No target.")
                return

            #process attack copy code
            new_weapon = copy_attack(char,caller)


        except ValueError:
            caller.msg(errmsg)
            return
        


class CmdAuraRead(MuxCommand):
    """
    Get a sense of how powerful a target is.

    Usage:
      auraread <target>

         

    """
    
    key = "auraread"
    aliases = ["+auraread"]
    help_category = "Powers"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg("You read an aura.")
        if not args:
            caller.msg("Read whose aura?")
            return
        

class CmdRequisition(MuxCommand):
    """
    Grab a temporary weapon from your cache to overcome a new obstacle.

    Usage:
      requisition <class>,<element>
    ex:
      requisition Ranged,Blade


    This capability allows a character to borrow a weapon from a cache they 
    might ICly have available. Only certain characters have access to this.
    
    When requisitioning a new weapon, it will be added to your weapon inventory as
    'Requisitioned (Class Type) Weapon.' Example: Requisitioned Thrown Ice Weapon.
    Weapons borrowed this way can only have one element attached to them, 
    and will have no flags or special abilities.

    Weapons which are acquired via requisition will vanish from your inventory
    after one week. Only one weapon can be requisitioned at a time. 
    

    """
    
    key = "requisition"
    aliases = ["+requisition"]
    help_category = "Powers"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args

        if not args:
            caller.msg("What type of weapon?")
            return


class CmdCommandeer(MuxCommand):
    """
    Temporarily roleplay as one of your subordinates.

    Usage:
      commandeer <target>

    

    """
    
    key = "commandeer"
    aliases = ["+commandeer"]
    help_category = "Powers"
    locks = "perm(Player)"

    def func(self):
        '''
        This should only show up if you have the skill
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg(f"You become {args}.")
        if not args:
            caller.msg("Commandeer who?")
            return
        
        caller.msg(f"You become {args}.")
        return
        
        
