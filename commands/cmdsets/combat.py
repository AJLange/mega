"""
Combat Related Commands

"""

from calendar import c
from commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi
from random import randint
from evennia import Command, InterruptCommand
from server.battle import roll_attack, check_valid_target, explode_tens, roll_to_string, check_successes, check_capabilities, copy_attack, do_roll, check_morale, check_not_ko
from evennia.utils.utils import inherits_from
from django.conf import settings
from world.combat.models import Weapon, GenericAttack
from world.armor.models import ArmorMode, Capability



'''
constants set here for testing purposes
'''

DUEL_HP = 90
STANDARD_HP = 60
DUEL_MORALE = 100
STANDARD_MORALE = 70
HP_FACTOR = 60
MORALE_FACTOR = 60
CRIT_FACTOR = 1.5
RESIST_FACTOR = 0.75


def combat_reset(player):
    player.db.hp = STANDARD_HP
    player.db.morale = STANDARD_MORALE
    player.db.aimdice = 0
    player.db.defending = 0
    player.db.chargedice = 0
    player.db.bonusdice = 0
    player.db.boss = False


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
    caller.db.athletics =  armor.db_athletics
    caller.db.force = armor.db_force
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


class CmdModeSwap(MuxCommand):
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
        
        errmsg = "Error, check help armor."
        caller= self.caller

        # TODO - emit to room and logs

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
            my_armors = caller.db.armor
            #handle multiple matches
            if len(armor_list > 1):
                for armor in armor_list:
                    for my_armor in my_armors:        
                        if my_armor.id == armor.id:
                            #match found, do the swap
                            swap_armor(caller,my_armor)
                            caller.msg(f"Swapped to {my_armor}.")
                            #set the name of the armor, for the sheet
                            caller.db.currentmode = my_armor.db_name
                            return
            else:
                # only one match so it's faster not to loop
                for my_armor in my_armors:
                    if my_armor.id == armor[0].id:
                        swap_armor(caller,my_armor)
                        caller.msg(f"Swapped to {my_armor}.")
                        #set the name of the armor, for the sheet
                        caller.db.currentmode = my_armor.db_name
                        return
                        

class CmdHPDisplay(MuxCommand):
    """
    Show my current HP.

    Usage:
        +hp
        hp
        health
        morale

    A future version might also allow certain characters to see the HP of others.
    This also shows your morale.

    """
        
    key = "hp"
    aliases = ["+hp","health", "+health", "morale", "+morale"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        caller = self.caller
        # build a string
        # TODO - make pretty 
        border = "________________________________________________________________________________"

        sheetmsg = (border + "HP: " + str(caller.db.hp) + "\n" + "Morale: " + str(caller.db.morale) + "\n" + border + "\n")
        caller.msg(sheetmsg)


class CmdShowdown(MuxCommand):
    """
    Starts a showdown.

    Usage:
        showdown 
        showdown/start
        showdown/boss
        showdown/boss <#>
        showdown/join
        showdown/end

    showdown with no switches checks on a combat in the room, if one is 
    active.

    showdown/join is if you came in late, and wish to be added to the active
    combat in progress. Please check with any bosses or DMs before adding yourself
    as they may have to adjust numbers.

    showdown/boss begins a showdown with the number of people specified,
    and the originator set as a 'boss' with boss HP. If no number is specified,
    the boss showdown will calculate on all players in the room not set as 
    an observer.

    +showdown/end ends your current combat.

    """
    
    key = "showdown"
    aliases= "+showdown"
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):
        
        
        #this isn't final, attack commands need to check for an active combat.
        
        caller= self.caller
        room = caller.location

        if self.switches:
            if "start" in self.switches:
                if room.db.protector == "Staff" and not caller.check_permstring("builders"):
                    caller.msg("You can't start a showdown here - it's protected by staff. Ask staff about using this room.")
                    return
                if room.db.protector:
                    caller.msg("This room has a +protector set, so make sure they were consulted about your combat if necessary.")

            # start the rest of the showdown here
            # make sure one isn't active already
            # set everyone as in an active combat if they are not set observer
            room.db.combat = True
            char_list = room.contents_get(exclude=caller.location.exits)                
            for player in char_list:
                #make sure it's a player and not some other object
                if inherits_from(player, settings.BASE_CHARACTER_TYPECLASS):
                    if not player.db.observer:
                        #remove all flags and bonus dice
                        player.db.incombat = True
                        combat_reset(player)
            if "boss" in self.switches:
                caller.msg("You start a boss fight in this location!")
                caller.location.msg_contents(caller.name + " has begun a Boss Showdown in this location!" )

                #check for override number supplied, if not, continue

                if self.args:
                    try:
                        override= int(self.args)
                    except:
                        caller.msg("Number must be an integer.")
                        return
                    if override > 20:
                        caller.msg("That is too many players.")
                        return
                
                '''
                Set HP based on the involved number of attackers
                start at -1 since a boss is not counted as themselves.
                '''
                    
                caller.db.incobmat = True
                caller.db.boss = True
                room.db.combat = True
                override = 0
                
                playercount = -1
                
                char_list = room.contents_get(exclude=caller.location.exits)
                
                for player in char_list:
                #make sure it's a player and not some other object
                    if inherits_from(player, settings.BASE_CHARACTER_TYPECLASS):
                        if not player.db.observer:
                            playercount += 1
                            # we have to check all players, to be sure this flag is set
                            player.db.incombat = True

                #boss HP takes the count, unless a hard number was specified
                if override:
                    playercount = override

                caller.db.hp = playercount * HP_FACTOR
                caller.db.morale = playercount * MORALE_FACTOR
                
                return
            if "join" in self.switches:
                if caller.incombat:
                    caller.msg("You are already in an active Showdown.")
                    return
                else:
                    caller.incombat = True
                    #TODO - bug check this to make sure it doesn't allow people to reset in the middle
                    #of an active fight
                    combat_reset(caller)

            if "end" in self.switches:
                #rooms don't have this flag by default
                #if it's there, a combat did happen, but ended
                room.db.combat = False          
                char_list = room.contents_get(exclude=caller.location.exits)                
                for player in char_list:
                #make sure it's a player and not some other object
                    if inherits_from(player, settings.BASE_CHARACTER_TYPECLASS):
                        #might not need this check, but leave it for now
                        if not player.db.observer:
                            #remove all flags and bonus dice
                            combat_reset(player)

            else:
                caller.msg("Invalid switch. See help showdown.")
                return
        else:
            #no switches, get status
            if not room.db.combat:
                caller.msg("No active Showdown is happening here.")
                return

            message = "Players in this Showdown: \n"
            char_list = room.contents_get(exclude=caller.location.exits)                
            for player in char_list:
                #make sure it's a player and not some other object
                if inherits_from(player, settings.BASE_CHARACTER_TYPECLASS):
                    if player.db.incombat:
                        # this is too much info for live, but now, for debugging, keep it.
                        message += (f"{player.name}: HP: {player.db.hp} Morale: {player.db.morale} \n")
            caller.msg(message)

        


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

class CmdRollSkill(MuxCommand):
    """
    Roll a Stat + Skill combo.

    Usage:
        check <stat> + <skill>
        check/focus <stat> + <skill>

    This allows any combination of rolls. Can be used to check any two stats.
    Useful in one-off confrontations, if trying to do something unusual, or
    if a particular roll is called by a GM in a Sequence.

    Currently it is not possible to check just a stat. Always choose
    which skill you want to roll. See news files for combo examples.

    check/focus is used when a skill is within your character's area of 
    focus and adds +2. Focuses are limited to what is on your sheet.

    """
    
    key = "check"
    aliases = ["+check"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

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
            outputmsg = ""

            if "focus" in self.switches:
                stat_check = stat_check + 1
                skill_check = skill_check + 1
                outputmsg += "Using a Focus: "

            # build the string

            result = do_roll(stat_check,skill_check)
            if len(result) == 0:
                caller.msg("Skill + stat combination invalid. Try again.")
                return
            else:
                result = explode_tens(result)
                successes = check_successes(result)
                str_result = roll_to_string(result)
                outputmsg += (f"{caller.name} rolls {stat} and {skill}: {str_result} \n" )
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
        
        errmsg = "An error occured. Contact an administrator to debug this."
        
        caller= self.caller
        sniper = False

        #if the Sniper capability is present, stack Aim up to 3x

        attacker_cap = check_capabilities(caller)

        for cap in attacker_cap:
            if cap == "Sniper":
                sniper = True

        if caller.db.aimdice == 1 and not sniper:
            caller.msg("You are already aiming!")
            return
        if caller.db.aimdice >= 3 and sniper:
            caller.msg("You are using the maximum amount of aim rounds.")
            return
        
        if not caller.db.incombat:
            caller.msg("You are not in an active action scene.")
            return
        
        alive = check_not_ko(caller)
        if not alive:
            caller.msg("You are KOed!")
            return
        
        try:
            caller.db.defending = 0
            caller.location.msg_contents(f"{caller.name} forfeits their turn to Aim.", from_obj=caller)
            caller.db.aimdice += 1
        except ValueError:
            caller.msg(errmsg)
            return


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
      attack/final <target>=<weapon>

    This will allow you to attack a target with a weapon you have equipped.

    If you don't specify a weapon, this will use the same weapon you used
    last time you attacked, provided that weapon is still available.

    Optionally, you can type 

    attack <target>=<weapon>|<Flavor text>

    This adds a little flavor text to the name of the weapon that you are 
    using. 

    Example:
    attack Bass=Mega Buster
    "Rock attacks Bass with Mega Buster!"

    attack Bass=Mega Buster||Charged Shot

    "Rock attacks Bass with Charged Shot (Mega Buster)!"

    Flavor text is optional and has zero impact on the attack rolls.

    attack/final is a last-ditch attempt for a more powerful attack, usually
    used at the end of a fight. It will always crit (do more damage), but will
    also guarantee that you will be hit if an attack is directed at you the 
    following round. Only one final attack can be used per combat.

    For more information check 'help combat'.

    """
    
    key = "attack"
    aliases = ["+attack"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        errmsg = "Sorry, an error occured."
        caller= self.caller
        switches = self.switches
        
        if not self.args:
            caller.msg("Attack who?")
            return
        attack_string = self.rhs
        target = self.lhs
        bonus_dice = 0
        result = 0
        attack_text = []
        try:
            #any target?
            msg = "Target not found."
            if not target:
                target = self.args.strip()

            alive = check_not_ko(caller)
            if not alive:
                caller.msg("You are KOed!")
                return

    
            char = self.caller.search(target, global_search=False)

            target_ok = check_valid_target(char)
            if not target_ok:
                caller.msg(msg)
                return
            
            target_alive = check_not_ko(char)
            if not target_alive:
                caller.msg("That target is already knocked out!")
                return
            
            #TODO - after alpha testing, make sure the combat flag is set on any target

            if not attack_string:
                if not caller.db.active_weapon:
                #there should be a value there, but if there isn't,
                #eg, I've changed armors to a mode that doesn't have that weapon anymore
                    caller.msg("Specify a valid weapon to use.")
                    return
                
            #start assuming name is name
            attack_name = attack_string
            try:
                attack_text = attack_string.split("|", 1)
            except:
                attack_name = attack_string

            if len(attack_text) > 1:
                flavor_text = attack_text[1]
                attack_name = attack_text[0]
            else:
                flavor_text = 0
                
            target = char
            weapon_check = Weapon.objects.filter(db_name__icontains=attack_name)
            my_weapons = caller.db.weapons
            weapon_generic = False
            
           
            # match found. Weapons should have a unique name with no duplicates.
            # this currently will fail on partial matches, so be more clever 
            # about this in the future.
            found_weapon = False
            for w in my_weapons:
                if weapon_check[0].id == w.id:                    
                    caller.msg(f"Using weapon {w.db_name}.")
                    caller.db.active_weapon = w
                    found_weapon = True
            
            if not found_weapon:
                # is it a generic weapon?
                weapon_check = GenericAttack.objects.filter(db_name__icontains=attack_name)
                if weapon_check:
                    found_weapon = True
                    weapon_generic = True
                    caller.db.active_weapon = weapon_check[0]
                else:
                    #no weapon no attack
                    caller.msg("That weapon is not in your arsenal.")
                    return
    
            #if I attack I'm not defending
            caller.db.defending = 0
            target_defense = target.db.ten
            target_cap = check_capabilities(target)
            attacker_cap = check_capabilities(caller)
            #either a stored weapon or the one just set
            weapon = caller.db.active_weapon

            if flavor_text:
                if len(flavor_text) > 65:
                    caller.msg("Please type a shorter flavor message")
                    return
                weapon_string = (f"{flavor_text} ({weapon.db_name})")
            else:
                weapon_string = weapon.db_name

            #is the target in full defense?
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

            #TODO - check - is the target being defended by anyone else?
            #if so, high chance of redirecting this attack.
            #higher if you have bodyguard

            which_stat, which_skill = roll_attack(caller, weapon)
            if which_stat == "random":
                rand1 = randint(1,10)
                rand2 = randint(1,10)
                result = do_roll(rand1,rand2)
            else:
                result = do_roll(which_stat,which_skill)
            # add aimdice to the to-hit
            if caller.db.aimdice:
                bonus_dice = caller.db.aimdice
                bonus = do_roll(bonus_dice,0)
                #not sure this works
                result = result + bonus
            str_result = str(result)
            dodge_roll = do_roll(target_defense,target.db.athletics)
            str_dodge = str(dodge_roll)
            
            caller.msg(f"You attack {char.name} with {weapon.db_name}.")

            outputmsg = (f"{caller.name} rolls to attack with {weapon_string}: {str_result} \n" )
            
            #primitive first draft damage calc. do better later.
            #TODO - no dodge roll if reckless target.

            damage = 0
            for die in result:
                damage = damage + int(die)
            for die in dodge_roll:
                damage = damage - int(die)
            
            #can't do negative damage
            if damage < 0:
                damage = 0

            #final attack damage
            if "final" in switches:
                damage = damage * 1.5
                caller.db.reckless = True
                outputmsg += (f"They're giving it their all!\n" )
            else:
                caller.db.reckless = False

            if target.db.reckless:
                #reckless targets can't defend.
                target_defense = 0
                outputmsg += (f"{target.name} used a final strike and can't defend! \n" )
            else:           
                outputmsg += (f"{target.name} defends with: {str_dodge}. \n" ) 

            #skip element check for generic weapons
            if not weapon_generic:
                weapon_elements = [weapon.db_type_1, weapon.db_type_2, weapon.db_type_3]
                for element in weapon_elements:
                    if element:
                        if element == char.db.weakness:
                            outputmsg += (f"It hit a weakness! \n")
                            damage = damage * CRIT_FACTOR
                    if element:
                        if element == char.db.resistance:
                            outputmsg += (f"It hit a resist! \n")
                            damage = damage * RESIST_FACTOR
            
            if damage == 0:
                outputmsg += (f"The attack misses." )
            else:
                damage = int(damage)
                outputmsg += (f"The attack does {str(damage)} physical damage." )
                target.db.hp = target.db.hp - damage

            caller.location.msg_contents(outputmsg, from_obj=caller)


            '''
            You attack <person> with <weapon>
            Rolling <stat> plus <skill>: # # # # # #
            The attack hit <person>'s weakness! Critical hit!
            '''
            
        except ValueError:
            caller.msg(errmsg)
            return
        

class CmdGenericAtk(MuxCommand):
    """
    List available generic weapons

    Usage:
      generic

    This lists generic weapons available to all players.
    Generic weapons are untyped and will not hit a weakness
    or resistance.

    """
    
    key = "generic"
    aliases = ["+generic"]
    help_category = "Dice"
    locks = "perm(Player))"

    def func(self):

        caller= self.caller
        weapons = GenericAttack.objects.all()
        msg = "Generic Attacks: \n"
        for weapon in weapons:
            msg += (f"{weapon.db_name}: {weapon.db_class} \n")
        caller.msg(msg)
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

        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return

        if not self.args:
            caller.msg("Taunt who?")
            return
        
        '''
        Commenting this out for now, but this check
        will be used when the game goes live 

        if not caller.db.incombat:
            caller.msg("You are not in an active Showdown.")
            return

        if not target.db.incombat:
            caller.msg("That target is not in this Showdown.")
            return
        '''

        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(char)
   
        if not valid_target:
            caller.msg("Not a valid target.")
            return
                  
        target_alive = check_not_ko(char)
        if not target_alive:
            caller.msg("That target is already knocked out!")
            return
        
        target_morale = check_morale(char)
        if not target_morale:
            caller.msg("That target has no morale.")
            return


        #calc highest of charisma, aura, tenacity, cunning
        stat = max(caller.db.chr, caller.db.aur, caller.db.ten, caller.db.cun)
        skill = caller.get_a_skill("presence")
        
        try:
            caller.db.defending = 0
            result = do_roll(stat, skill)
            str_result = roll_to_string(result)
            dodge_roll = do_roll(char.db.cun, char.db.convince)
            outputmsg = (f"{caller.name} rolls to taunt: {str_result} \n" )

            #primitive first draft damage calc
            damage = 0
            for die in result:
                damage = damage + int(die)
            for die in dodge_roll:
                damage = damage - int(die)
            
            #can't do negative damage
            if damage < 0:
                damage = 0
            
            if damage == 0:
                outputmsg += (f"The attack misses." )
            else:
                outputmsg += (f"The attack does {str(damage)} morale damage." )
                char.db.morale = char.db.morale - damage

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
        
        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return

        if not self.args:
            caller.msg("Intimidate who?")
            return
        
        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return

        target_alive = check_not_ko(char)
        if not target_alive:
            caller.msg("That target is already knocked out!")
            return
        
        target_morale = check_morale(char)
        if not target_morale:
            caller.msg("That target has no morale.")
            return

        '''
        Commenting this out for now, but this check
        will be used when the game goes live 

        if not caller.db.incombat:
            caller.msg("You are not in an active Showdown.")
            return

        if not target.db.incombat:
            caller.msg("That target is not in this Showdown.")
            return
        '''

        #calc highest of charisma, aura, power
        stat = max(caller.db.chr, caller.db.aur, caller.db.pow)

        skill = caller.get_a_skill("presence")
        #TODO - if this roll fails, future difficulties are harder

        try:
            caller.db.defending = 0
            result = do_roll(stat, skill)
            str_result = roll_to_string(result)
            dodge_roll = do_roll(char.db.ten, char.db.presence)
            outputmsg = (f"{caller.name} rolls to intimidate: {str_result} \n" )

            #primitive first draft damage calc
            damage = 0
            for die in result:
                damage = damage + int(die)
            for die in dodge_roll:
                damage = damage - int(die)
            
            #can't do negative damage
            if damage < 0:
                damage = 0
            
            if damage == 0:
                outputmsg += (f"The attack misses." )
            else:
                outputmsg += (f"The attack does {str(damage)} morale damage." )
                char.db.morale = char.db.morale - damage

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

        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return

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
        
        # there were args, so guard someone
        # check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return

        #you can guard someone who is knocked out if you really want to


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

        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return
        
        if not self.args:
            caller.msg("Heal who?")
            return

        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(char)
        
        if not valid_target:
            caller.msg("Not a valid target.")
            return
        # no check for KO, it's Ok to heal someone who is KOed
        
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

        if not check_not_ko(caller):
            caller.msg("You are KOed!")
            return
        
        if not self.args:
            caller.msg("Persuade who?")
            return

        #check target is valid
        target = self.args.strip()
        char = self.caller.search(target, global_search=False)
        valid_target = check_valid_target(char)

        if not valid_target:
            caller.msg("Not a valid target.")
            return
        

        target_alive = check_not_ko(char)
        if not target_alive:
            caller.msg("You can't persuade someone who is KOed.")
            return
        
        target_morale = check_morale(char)
        if not target_morale:
            caller.msg("That target has no morale.")
            return
        
        '''
        Commenting this out for now, but this check
        will be used when the game goes live 

        if not caller.db.incombat:
            caller.msg("You are not in an active Showdown.")
            return

        if not target.db.incombat:
            caller.msg("That target is not in this Showdown.")
            return
        '''
        
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
            # TODO - update this dodge roll later and make it better
            dodge_roll = do_roll(char.db.ten, char.db.presence)
            outputmsg = (f"{caller.name} rolls to persuade: {str_result} \n" )

            #primitive first draft damage calc
            damage = 0
            for die in result:
                damage = damage + int(die)
            for die in dodge_roll:
                damage = damage - int(die)
            
            #can't do negative damage
            if damage < 0:
                damage = 0
            
            if damage == 0:
                outputmsg += (f"The attack misses." )
            else:
                outputmsg += (f"The attack does {str(damage)} morale damage." )
                char.db.morale = char.db.morale - damage

            caller.location.msg_contents(outputmsg, from_obj=caller)
        # TODO - if this roll fails, future difficulties are harder

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



