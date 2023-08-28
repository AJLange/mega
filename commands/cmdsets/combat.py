"""
Combat Related Commands

"""

from calendar import c
from evennia import CmdSet
from commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi
from random import randint
from evennia import Command, InterruptCommand
from server.battle import roll_attack, check_valid_target, explode_tens, roll_to_string, check_successes, check_capabilities, copy_attack, do_roll
from evennia.utils.utils import inherits_from
from django.conf import settings
from world.combat.models import Weapon
from world.armor.models import ArmorMode, Capability

'''
constants set here for testing purposes
'''

DUEL_HP = 90
STANDARD_HP = 60

"""
Combat is a type of scene called a Showdown which can be initiated via a showdown command
"""

def swap_armor(caller, armor):    

        #armor was found, so replace my stats with this armor
        caller.db.pow = armor.db_pow
        caller.db.dex = armor.db_dex
        caller.db.ten = armor.db_ten
        caller.db.cun = armor.db_cun
        caller.db.edu = armor.db_edu
        caller.db.chr = armor.db_chr
        caller.db.aur = armor.db_aur

        caller.discern = armor.db_discern
        caller.db.aim = armor.db_aim
        caller.db.athletics =  armor.db_
        caller.db.force = armor.db_athletics
        caller.db.mechanics = armor.db_mechanics
        caller.db.medicine = armor.db_medicine
        caller.db.computer = armor.db_computer
        caller.db.stealth = armor.db_stealth
        caller.db.heist = armor.db_heist
        caller.db.convince =  armor.db_convince
        caller.db.presence = armor.db_presence
        caller.db.arcana = armor.db_arcana

        caller.db.size = armor.db_size
        caller.db.speed = armor.db_speed
        caller.db.strength = armor.db_strength

        #right now, changing armors does not change buster list
        caller.db.capabilities = armor.db_capabilities
        caller.db.weapons = armor.db_weapons
        caller.db.primary = armor.db_primary
        caller.db.secondary = armor.db_secondary

        #process the armor message
        #TODO - better pronoun processing
        swap_msg = (f"{caller} activates their {armor.db_name} armor!")
        if armor.db_swap == 1:
            swap_msg = (f"{caller} has activated their {armor.db_name} mode!")
        elif armor.db_swap == 2:   
            swap_msg = (f"{caller} has swapped to their {armor.db_name} stance!")
        elif armor.db_swap == 3:
            swap_msg = (f"{caller} focuses their efforts, becoming {armor.db_name} !")
        elif armor.db_swap == 4:
            swap_msg = (f"{caller} changes forms, becoming their {armor.db_name}!")
        elif armor.db_swap == 5:
            swap_msg = (f"{caller} jacks in, activating {armor.db_name}!")
        elif armor.db_swap == 6:
            swap_msg = (f"{caller} summons {armor.db_name} to assist!")
        elif armor.db_swap == 7:
            swap_msg = (f"{caller} is playing as squadron {armor.db_name}.")
        elif armor.db_swap == 8:
            swap_msg = (f"{caller} activates their {armor.db_name} system!")

        # the generic '9' is currently a catch-all
        caller.location.msg_contents(swap_msg, from_obj=caller)
        return


class ModeSwap(MuxCommand):
    """
    Swap armor modes.

    Usage:
        armor <name>

    Swapping to an armor mode.
    This will change your stats and the weapons that you have equipped.


    """
    key = "armor"
    aliases= "+armor"
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        
        #stubbed only
        errmsg = "Error, check help armor."
        caller= self.caller

        if not self.args:
            caller.msg("Swap to which armor?")
            return
        else:
            # search the armor DB for a matching armor (not case sensitive)
            armor_name = self.args
            armor_list = ArmorMode.objects.filter(db_name__icontains=armor_name)
            errmsg = "No match for that armor was found."
            # did not find, return error
            if not armor_list:
                caller.msg(errmsg)
                return
            #handle multiple matches
            my_armors = caller.armor
            for my_armor in my_armors:
                for armor in armor_list:
                    if my_armor.id == armor.id:
                        #match found, do the swap
                        swap_armor(caller,my_armor)
                        caller.msg("Swapped.")
                        return
                    else:
                        caller.msg(errmsg)
                        return
            #TODO: change my desc based on the armor mode

        

class CmdShowdown(Command):
    """
    Starts a showdown.

    Usage:
        showdown <name>
        showdown/boss
        showdown/end

    showdown with a single name challenges that person to a duel.
    showdown/boss begins a showdown with everyone in the room who is not
    set as observer.

    +showdown/end ends your current combat if you are a boss or duelist.

    This is currently not balanced for 2 on 1 or other configurations.
    A duel in progress can't be third-partied. However, multiple
    boss fights can be initiated in the same location.

    """
    
    key = "showdown"
    aliases= "+showdown"
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        '''
        doesn't function yet just stubbing out commands.

        to-do: test balance for other configurations.
        occupied check needs to sync with db in case of reset.

        '''
        errmsg = "You must supply a target, or choose +showdown/boss to attack everyone."
        
        occupied = False
        caller= self.caller
        room = caller.location

        if room.db.protector == "Staff" and not caller.check_permstring("builders"):
            caller.msg("You can't start a showdown here - it's protected by staff. Ask staff about using this room.")
            return
        if room.db.protector:
                caller.msg("This room has a +protector set, so make sure they were consulted about your combat if necessary.")
        if self.switches or self.args:
            if "boss" in self.switches:
                caller.msg("You start a boss fight in this location!")
                caller.location.msg_contents(caller.name + " has begun a Boss Showdown in this location!" )

                '''
                what needs to happen:
                Set HP based on the involved number of attackers
                check if the room has a protector, return a warning if it does.
                '''
            if "end" in self.switches:
                caller.db.hp = STANDARD_HP
                ''' 
                remove everyone's aimdice and bonus dice
                '''

        if not self.args:
            caller.msg(errmsg)
            return
        try:
            '''
            do-to: error check - is target a character? are they in the room?
            '''
            target = self.args
            caller.msg(f"You start a showdown with {target.name}.")
            target.msg(f"{caller.name} has challenged you a duel!")
            ''' 
            set duel HP
            '''
            target.db.hp = DUEL_HP
            caller.db.hp = DUEL_HP

            if not (occupied):
                occupied = True
                return
            else:
                caller.msg("That person is already in a duel.")
        except ValueError:
            caller.msg(errmsg)
            return


class CmdGMRoll(Command):
    """
    GM free rolls a certain amount of dice.

    Usage:
       gmroll <number from 1-10>

    This is for if you just need to roll D10s for whatever reason in a 
    scene you may be running. Unlike most standard rolls, this roll does not
    have exploding 10s.

    To roll a die with an arbitrary amount of sides, see +roll.

    """
    
    key = "gmroll"
    aliases = ["+gmroll"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Roll how many dice?")
            return
        '''convert argument to a number'''
        args = self.args.lstrip()
        try:
            numdice = int(args)
            if not 1 <= numdice <=10:
                raise ValueError
        except ValueError:
            caller.msg("Number of dice must be an integer between 1 and 10.")
            raise InterruptCommand

        result = list(range(numdice))
        outputmsg = (f"{caller.name} does a GM roll: ")
        errmsg = "An error occured."
        for i in range(0, numdice):
            random = randint(1,10)
            result[i] = random
        successes = check_successes(result)
        outputmsg +=  roll_to_string(result)
        outputmsg += "\n" + str(successes) + " successes."
        try:
            caller.location.msg_contents(outputmsg, from_obj=caller)
        except ValueError:
            caller.msg(errmsg)
            return


class CmdRoll(Command):
    """
    Roll an arbitrary die.

    Usage:
       roll <number from 1-100>

    This will choose a random integer, depending on the size of the die you 
    choose to roll. This is a purely random choice to be used for arbitrary 
    decision making.

    Rolling a die other than 1d10 is not an official game mechanic or part of
    the combat system, but can sometimes be useful.

    """
    
    key = "roll"
    aliases = ["+roll"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        errmsg = "An error occured."
        caller = self.caller

        if not self.args:
            caller.msg("Roll what size die?")
            return
        '''convert argument to a number'''
        args = self.args.lstrip()
        try:
            dice = int(args)
            if not 1 <= dice <=100:
                raise ValueError
        except ValueError:
            self.msg("Please choose a die size as an integer between 1 and 100.")
            raise InterruptCommand

        result = randint(1,dice)
        name = caller.name
        try:
            message = (f"{name} rolls a D{dice} and rolls a {result}.")
            caller.location.msg_contents(message, from_obj=caller)

        except ValueError:
            caller.msg(errmsg)
            return


class CmdFlip(Command):
    """
    Flip a coin.

    Usage:
       +flip

    This command flips a coin, with a result of heads or tails.

    There are two uses for this command. One is of an OOC nature, when
    you may just be trying to choose between two outcomes. If you 
    need to choose between more than two possible outcomes, see +roll.

    This command may also be used to indicate an IC flip of a coin, as 
    in the opening round of a Battle and Chase sporting match, or for
    other dramatic reasons.

    Please note that when the coin flip mechanic is used IC, some characters
    do have the ability to cheat on the coin flip.

    """
    
    key = "flip"
    aliases = ["+flip"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        caller = self.caller
        errmsg = "An error occured."

        '''
        to do: cheating stuff.
        '''
        try:
            result = randint(0,1)
            if result == 1:
                str_result = "|rheads.|n"
            else:
                str_result = "|gtails.|n"
            outputmsg = (f"{caller.name} flips a coin in the air and it comes down {str_result}" )
            caller.location.msg_contents(outputmsg, from_obj=caller)
        except ValueError:
            caller.msg(errmsg)
            return


'''
holding this space, might not use this command

class CmdStatRoll(Command):
    """
    Stat roll an individual stat. Useful for a quick check.

    Usage:
      +statroll <stat>
      +statroll Aur


    """
    
    key = "+statroll"
    aliases = ["statroll"]
    help_category = "Dice"

    def func(self):

        errmsg = "An error occured."
        
        caller= self.caller
        
        if not self.args:
            caller.msg("Roll which stat?")
            return
        try:
            self.caller.msg("You Roll.")
        except ValueError:
            caller.msg(errmsg)
            return
'''

class CmdRollSkill(Command):
    """
    Roll a Stat + Skill combo.

    Usage:
        check <stat> + <skill>

    This allows any combination of rolls. Can be used to check any two stats.
    Useful in one-off confrontations, if trying to do something unusual, or
    if a particular roll is called by a GM in a Sequence.

    Currently it is not possible to check just a stat. Always choose
    which skill you want to roll. See news files for combo examples.

    """
    
    key = "check"
    aliases = ["+check"]
    help_category = "Dice"
    locks = "perm(Player))"


    def func(self):

        #todo: any bonus dice that need added might be added?

        caller = self.caller
        errmsg = "Wrong syntax. Please enter a valid stat and skill seperated by +."
        if not self.args:
            caller.msg(errmsg)
            return
        args = self.args
        try:
            stat, skill = args.split("+",1)
            stat = stat.strip()
            skill = skill.strip()
        except ValueError:
            caller.msg(errmsg)
            return
        
        errmsg = "An error occured. Contact staff to help debug this."
        
        try:
            stat_check = caller.get_a_stat(stat)
            skill_check = caller.get_a_skill(skill)

            # build the string

            result = do_roll(stat_check,skill_check)
            if len(result) == 0:
                caller.msg("Skill + stat combination invalid. Try again.")
                return
            else:
                result = explode_tens(result)
                successes = check_successes(result)
                str_result = roll_to_string(result)
                outputmsg = (f"{caller.name} rolls {stat} and {skill}: {str_result} \n" )
                outputmsg += (f"{successes} successes.")
                caller.location.msg_contents(outputmsg, from_obj=caller)
            
        except ValueError:
            caller.msg(errmsg)
            return

'''
+Aim - sacrifice a round for a higher chance of hitting next round.
+Charge - sacrifice around for a higher crit chance next round. If a charge crit hits 
a weakness it does triple damage.
+Assist - sacrifice your round to add your dice to another player's roll.
+Heal (this has several varieties)
+Guard - sacrifice a round to counter/deflect
+Taunt - presence roll to do damage. Makes it slightly harder for target to 
hit other people next round
+intimidate - presence roll to do damage. Makes it slightly harder for 
target to hit you next round
+Persuade/+negotiate/+moralhighground - make a convince roll to do damage
'''

class CmdAim(Command):

    """

    Usage:
        aim

    Sacrifice a combat round for a higher chance of hitting next 
    time you +attack.

    Only can be used in a Sequence or Showdown.

    An aim will be held until an +attack is used, or the 
    Sequence/Showdown is over. If the scene ends before you
    +attack, the aiming action is lost.

    """
    
    key = "aim"
    aliases = ["+aim"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        
        errmsg = "An error occured."
        
        caller= self.caller

        if caller.db.aimdice == 1:
            caller.msg("You are already aiming!")

        '''
        future check: if the Sniper capability is present, stack Aim up to 3x
        '''

        try:
            caller.db.defending = 0
            caller.location.msg_contents(f"{caller.name} forfeits their turn to Aim.", from_obj=caller)
            caller.db.aimdice = 1
        except ValueError:
            caller.msg(errmsg)
            return
        '''
        todo: remember to clear out aimdice if combat ends
        '''


class CmdCharge(Command):

    """
    Usage:
        charge

    Sacrifice a combat round for a higher crit chance next round,
    provided your next action is an +attack.

    If a charge crit hits a weakness, it does triple damage.

    Only can be used in a Sequence or Showdown.
    
    A charge will be held until an +attack is used, or the 
    Sequence/Showdown is over. If the scene ends before you
    +attack, the charge is lost.

    """
    
    key = "charge"
    aliases = ["+charge"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        '''
        doesn't function yet just stubbing out commands.
        '''
        errmsg = "An error occured."
        
        caller= self.caller

        if caller.db.chargedice == 1:
            caller.msg("You can't charge any more!")

        '''
        future check: if the Megablast capability is present, stack Charge up to 3x
        '''
        
        try:
            caller.db.defending = 0
            caller.location.msg_contents(f"{caller.name} is charging their shot!", from_obj=caller)
            caller.db.chargedice = 1
        except ValueError:
            caller.msg(errmsg)
            return

class CmdAttack(MuxCommand):
    """
    Attacking a particular target. 

    Usage:
      attack <target>=<weapon>
      attack <target>

    This will allow you to attack a target with a weapon you have equipped.

    If you don't specify a weapon, this will use the same weapon you used
    last time you attacked, provided that weapon is still available.

    """
    
    key = "attack"
    aliases = ["+attack"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "Sorry, an error occured."
        caller= self.caller
        
        if not self.args:
            caller.msg("Attack who?")
            return
        weapon = self.rhs
        target = self.lhs
        bonus_dice = 0
        result = 0
        try:
            #any target?
            msg = "Target not found."
            if not target:
                caller.msg(msg)
                return

            #is it a character/valid target?
            target_ok = check_valid_target(target)
            if not target_ok:
                caller.msg(msg)
                return

            if not weapon:
                if caller.db.active_weapon:
                    weapon = caller.db.active_weapon
                #there should be a value there, but if there isn't,
                #eg, I've changed armors to a mode that doesn't have that weapon anymore
                else:
                    caller.msg("Specify a valid weapon to use.")
                    return
            
            char = self.caller.search(target, global_search=False)
    

            #if I attack I'm not defending
            caller.db.defending = 0
            target_defense = target.db.ten
            target_cap = check_capabilities(target)

            # don't need for now
            # attacker_cap = check_capabilities(caller)

            #to check: is the target in full defense?
            #if so, if target is defender, no damage can be done
            #otherwise, lower the potential to-hit
            full_defender = False
            if target.db.defending:
                for cap in target_cap:
                    if cap == "Defender":
                        full_defender = True

                if full_defender:
                    outputmsg = (f"{caller.name} tries to attack, but {target.name} is in full defense!" )
                    return
                else:
                    #right now defending gives 2x tenacity skill, may change
                    target_defense = int(target_defense * 2)
            
            #to check: is the target being defended by anyone else?
            #if so, high chance of redirecting this attack.
            #higher if you have bodyguard

            which_stat, which_skill = roll_attack(weapon)
            if which_stat == "random":
                rand1 = randint(1,10)
                rand2 = randint(1,10)
                result = do_roll(rand1,rand2)
            else:
                result = do_roll(which_stat,which_skill)
            # add aimdice to the to-hit
            if self.db.aimdice:
                bonus_dice = self.db.aimdice
                bonus = do_roll(bonus_dice,0)
                result = result + bonus
            str_result = str(result)
            dodge_roll = do_roll(target_defense,target.db.athletics)
            str_dodge = str(dodge_roll)
            
            caller.msg("You attack %s with %s." % str(char), weapon)
            outputmsg = (f"{caller.name} rolls to attack: {str_result} \n" )
            outputmsg += (f"{target.name} defends with: {str_dodge}." )
            caller.location.msg_contents(outputmsg, from_obj=caller)

            #still to do: types, damage

            '''
            You attack <person> with <weapon>
            Rolling <stat> plus <skill>: # # # # # #
            The attack hit <person>'s weakness! Critical hit!
            '''
            
        except ValueError:
            caller.msg(errmsg)
            return


class CmdTaunt(MuxCommand):

    """

    taunt <target>

    This type of assail makes a presence roll to do damage. Using this makes 
    it slightly harder for your target to hit other people next round, 
    but slightly easier to hit you.

    Only can be used in a Sequence or Showdown.

    """
    
    key = "taunt"
    aliases = ["+taunt"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "An error occured."
        caller= self.caller

        if not self.args:
            caller.msg("Taunt who?")
            return
        
        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(self, char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return

        #calc highest of charisma, aura, tenacity, cunning
        stat = max(caller.db.chr, caller.db.aur, caller.db.ten, caller.db.cun)
        skill = caller.get_a_skill("presence")
        
        try:
            caller.db.defending = 0
            result = do_roll(stat, skill)
            str_result = roll_to_string(result)
            outputmsg = (f"{caller.name} rolls to taunt: {str_result}" )
            caller.location.msg_contents(outputmsg, from_obj=caller)
        except ValueError:
            caller.msg(errmsg)
            return


class CmdIntimidate(MuxCommand):

    """

    intimidate <target>

    This type of assail makes a presence roll to do damage. Using this makes 
    it slightly harder for your target to hit you next round.

    Only can be used in a Sequence or Showdown.
    
    Only can be used once per target per Sequence/Showdown. The effect
    does not stack.

    """
    
    key = "intimidate"
    aliases = ["+intimidate", "spook", "+spook"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "An error occured."        
        caller= self.caller
        
        if not self.args:
            caller.msg("Intimidate who?")
            return
        
        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(self, char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return

        #calc highest of charisma, aura, power
        stat = max(caller.db.chr, caller.db.aur, caller.db.pow)

        skill = caller.get_a_skill("presence")

        try:
            caller.db.defending = 0
            result = do_roll(stat, skill)
            str_result = roll_to_string(result)
            outputmsg = (f"{caller.name} rolls to intimidate: {str_result}" )
            caller.location.msg_contents(outputmsg, from_obj=caller)
        except ValueError:
            caller.msg(errmsg)
            return

class CmdGuard(MuxCommand):

    """
    Usage:
        guard 
        guard <target>

    Go fully defensive this round, making it quite a bit
    harder to be attacked or damaged, but at the cost of any
    meaningful action this turn.

    If guard is used on a target, this instead makes you 
    more likely to hit, but less likely for that target to be hit.
    
    Choose wisely.

    The guard command has no effect on attempts to pursuade.

    If your character has the Defender capability, they will take
    no damage when in full guard.

    Only can be used in a Sequence or Showdown.

    """
    
    key = "guard"
    aliases = ["+guard"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "An error occured."
        caller= self.caller

        if not self.args:
            outputmsg = (f"{caller.name} goes into full defense." )
            caller.location.msg_contents(outputmsg, from_obj=caller)
            caller.db.defending = 1
            return
        try:
            self.caller.msg("You Roll.")
        except ValueError:
            caller.msg(errmsg)
            return

class CmdHeal(Command):

    """

    heal <target>

    Don't really know how to balance this yet, won't 
    implement in early alpha.

    Only can be used in a Sequence or Showdown.

    """
    
    key = "heal"
    aliases = ["+heal"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "An error occured."
        caller= self.caller

        
        errmsg = "An error occured."        
        caller= self.caller
        
        if not self.args:
            caller.msg("Heal who?")
            return

        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(self, char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return
        
        if not self.args:
            caller.msg("Roll how many dice?")
            return
        try:
            self.caller.msg("You Roll.")
        except ValueError:
            caller.msg(errmsg)
            return


class CmdPersuade(Command):

    """
    Usage:
      persuade <target>

    This type of assail uses your convince skill to do damage to a target.

    Only can be used in a Sequence or Showdown.

    """
    
    key = "persuade"
    aliases = ["+persuade", "negotiate" ,"+negotiate", "moralhighground" , "+moralhighground"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "An error occured."        
        caller= self.caller
        
        if not self.args:
            caller.msg("Heal who?")
            return

        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(self, char)

        if not valid_target:
            caller.msg("Not a valid target.")
            return
        
        '''
        todo: apply any bonus dice for pose or circumstance
        '''

        #calc highest of charisma, cunning, education
        stat = max(caller.db.chr, caller.db.cun, caller.db.edu)
        skill = caller.get_a_skill("convince")

        try:
            caller.db.defending = 0
            result = do_roll(stat, skill)
            str_result = roll_to_string(result)
            outputmsg = (f"{caller.name} rolls to persuade: {str_result}" )
            caller.location.msg_contents(outputmsg, from_obj=caller)
        except ValueError:
            caller.msg(errmsg)
            return


class CmdRollSet(MuxCommand):
    """
    Usage:
      rollset
      rollset/verbose
      rollset/basic

    Swap between die view modes. Setting rollset to 'verbose' will show all of the 
    individual roles that lead to a die result. Setting to 'basic' will only show
    the final narrative result. 

    +rollset on its own toggles between these two readout modes.

    """
    
    key = "rollset"
    aliases = ["+rollset"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        '''
        Doesn't function yet. Just sets the value to allow this to function in the future.
        '''
        errmsg = "A value error occured. Contact staff about this error."
        
        caller = self.caller

        '''
        rollset 1 is verbose. rollset 2 is basic.

        if there's no switch, check current value and toggle.
        '''

        if not self.switches:
            if caller.db.rollset == 1:
                caller.db.rollset = 2
                caller.msg("Set roll view type to basic.")
                return
            elif caller.db.rollset == 2:
                caller.db.rollset = 1
                caller.msg("Set roll view type to verbose.")
                return
            else:
                caller.msg(errmsg)        

        '''
        had a switch, so just set the value
        '''

        if "verbose" in self.switches:
            caller.db.rollset = 1
            caller.msg("Set roll view type to verbose.")
            return
        elif "basic" in self.switches:
            caller.db.rollset = 2
            caller.msg("Set roll view type to basic.")
            return
        else:
            caller.msg("Not a valid choice. Choose verbose or basic.")
            return



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
    locks = "perm(Player))"

    def func(self):
        '''
        To-do: this command should not show up if you can't do it.
        check permission locks on how to achieve this.
        '''
        errmsg = "An error occured."
        
        caller= self.caller
        args = self.args
        caller.msg("Initiating weapon copy.")
        if not args:
            caller.msg("Copy whose weapon?")
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