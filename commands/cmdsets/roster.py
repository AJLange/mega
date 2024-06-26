"""
commands related to groups and rosters

Commands not hooked into the system yet - make sure PCs are created before testing.

"""

# TODO - valid char check is a bit messy, refactor it later

from evennia import CmdSet
from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from world.pcgroups.models import Squad, PlayerGroup
from world.roster.models import GameRoster
from evennia.utils import evmenu
from evennia.utils.search import object_search
from evennia.utils.utils import inherits_from
from server.utils import color_check
from django.conf import settings
from typeclasses.objects import Object
from evennia.objects.models import ObjectDB


def get_group(caller, name):
    groups = PlayerGroup.objects.filter(db_name__icontains=name)
    if not groups:
        #no group found.
        return 0

    else:
        return groups[0]
    

def check_char_valid(caller, char):
    if not char:
        caller.msg("Character not found.")
        return 0
    if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
        caller.msg("Character not found.")
        return 0
    else:
        return char


class CmdSetGroups(MuxCommand):
    """
    Adding a character to a particular group.

    Usage:
      +addgroup <person>=<group>

    Adds a character to a group of which you are a leader. This is only available
    to admin and to characters who have a leadership position in a group. 

    +ally is an alias for +addgroup but there is no sense of being just an ally
    of a group. You are either a member or not a member.

    """
    
    key = "+addgroup"
    aliases = ["ally", "addgroup", "+ally"]
    help_category = "Roster"

    def groupadd(caller, char_string, name):        
        #choosing first match
        group = get_group(caller, name)
        if group:
            #make sure that's a valid character
            char = caller.search(char_string, global_search=True)

            char = check_char_valid(caller,char)
            if not char:
                caller.msg("Character not found.")
                return
            
            group.db_members.add(char)
            char.db.pcgroups.append(group.db_name)
            caller.msg(f"Added {char.name} to the group {group.db_name}.")
            char.msg(f"You were added to the group {group.db_name}.")
            return
        else:
            caller.msg("Error occured. Check the group name or contact admin.")
            return

    def func(self):
        
        caller = self.caller
        errmsg = "Syntax error - check help addgroup"
        args = self.args

        if not args:
            caller.msg(errmsg)
            return

        try:
            group = self.rhs
            char_string = self.lhs
        except ValueError:
            caller.msg(errmsg)
            return
        char = caller.search(char_string, global_search=True)
        char = check_char_valid(caller,char)
        if not char:
            return
            
        my_group = get_group(caller,group)
        # am I admin?
        if caller.check_permstring("builders"):
            self.groupadd(caller, char, group)
            return
        # am I in that group?
        else:
            for member in my_group.db_members:
                if member == char:
                    #TODO - if rank above a number. not checking this for now
                    self.groupadd(caller,char,group)
                    return
                else:
                    caller.msg(f"You aren't a member of the group {group}.")
                    return

class CmdCreateSquad(MuxCommand):
    """
    Adding a new squad to a group.

    Usage:
      +addsquad <group>=<squad name>

    Adds a squad to a group of which you are a leader. This is only available
    to admin and to characters who have a leadership position in a group. 

    Squads are created empty. To add a character to a squad, use the +rank
    command.

    """
    
    key = "+addsquad"
    aliases = ["addsquad"]
    help_category = "Roster"


    def func(self):
        "This performs the actual command"
        errmsg = "Syntax error. Check help +addsquad."
        caller = self.caller
        if not self.args:
            caller.msg(errmsg)
            return

        try:
            group_name = self.lhs
            squad = self.rhs
            group = get_group(caller,group_name)
            if not group:
                caller.msg("Error, group not found.")
                return
            # am I admin?
            if caller.check_permstring("builders"):
                if squad:
                    if squad == group_name:
                        caller.msg("Please choose a unique name.")
                        return
                    try:
                        # TODO - make sure squad name isn't duplicate.
                        new_squad = Squad.objects.create(db_name = squad, db_group=group)  
                        caller.msg(f"Added the new squad {new_squad.db_name} to the group {group}")
                        return
                    except:
                        caller.msg("Syntax error occured.")
                        return
                else:
                    caller.msg("No squad specified.")
                    return
            # am I in that group?
            else:
                for member in group.db_members:
                    if member == caller:
                        # TODO - Check for leadership
                        if squad == group_name:
                            caller.msg("Please choose a unique name.")
                            return
                        try:
                            # TODO - make sure squad name isn't duplicate.
                            new_squad = Squad.objects.create(db_name = squad, db_group=group)  
                            caller.msg(f"Added the new squad {new_squad.db_name} to the group {group}")
                            return
                        except:
                            caller.msg("Syntax error occured.")
                            return
                else:
                    caller.msg(f"You aren't a member of the group {group}.")
                    return

        
        except ValueError:
            self.caller.msg(errmsg)
            return
        

class CmdSetRank(MuxCommand):
    """
    Set the rank of a character.

    Usage:
      +rank <character>=<group or squad>/<number>
      ex:
      +rank Metal Man=Robot Masters/5
      +rank Metal Man=Beta/5

      +rank/remove <character>=<squad>

    This command is only used in groups which have a rank and squad setup.
    If the character is not already in that squad, it will move them to 
    that squad. If the character is already in that squad, it will just
    adjust their rank in that squad.

    Setting ranks is entirely optional.

    Squads are not mutually exclusive, allowing for nuanced setting of 
    ranks or use for temporary assignments. Use +rank/remove to take a 
    character out of a squad, which will also delete their rank in 
    that squad.

    Squads that are empty will no longer appear on the group roster.

    """
    
    key = "+rank"
    aliases = ["rank", "setrank","+setrank"]
    help_category = "Roster"

    def find_squad(caller, squad_name):
        squad = Squad.objects.filter(db_key__icontains=squad_name)
        # right now I'm not handling duplicate squad names very well
        if len(squad) > 1:
            caller.msg("Similarly named squads. Type a more precise squad search. If you think this is a bug, contact admin.")
            return squad
        if not squad:
            caller.msg("That squad was not found in your group.")
            return 0

    def func(self):
        caller= self.caller
        errmsg = "Syntax Error - check help +rank."

        if not self.args:
            self.caller.msg(errmsg)
            return

        try:
            set_string = self.rhs
            char_string = self.lhs
        except ValueError:
            caller.msg(errmsg)
            return
        
        char = caller.search(char_string, global_search=True)
        char = check_char_valid(caller,char)
        if not char:
            caller.msg("Character not found.")
            return
        


        if "remove" in self.switches:
            # is this character in that squad? Assume only a squad was provided.
            squad = self.find_squad(caller,set_string)
            if not squad:
                caller.msg("No Squad found")
                return
            # remove them
            for sq in char.db.squads:
                if sq == squad.db_name:
                    #squad found, remove squad and rank
                    squad.db_members.remove(char)
                    my_squads = char.db.squads()
                    for s in my_squads:
                        if s == squad_name:
                            i = my_squads.index(s)
                            del char.db.squads[i]
                            del char.db.squads[i+1]
                    caller.msg(f"Removed {char} from Squad {squad.db_name}.")
                    return

            #nothing worked, so there was an error
            caller.msg("That character does not appear to be in that squad.")
            return        

        try:
            #parse the split variable            
            text = set_string.split("/")
            squad_name = text[0]
            rank_num = int(text[1])
        except ValueError:
            self.caller.msg(errmsg)
            return
        
        # did i specify a group or a squad?
        is_group = PlayerGroup.objects.filter(db_key__icontains=squad_name)
        all_groups = PlayerGroup.objects.all()
        can_add = False

        # this might cause bugs if a squad is named similiarly to a group. TODO
        if not is_group:
            squad = Squad.objects.filter(db_key__icontains=squad_name)
        else:
            squad = is_group
        # am I admin?
        if caller.check_permstring("builders"):
            can_add = True
        else:
            # do I have authority?
            for group in caller.db.pcgroups:
                if group.db_leader == caller or group.db_twoic == caller:
                    if is_group and group == squad_name:
                    # adjusting rank in a group I lead                    
                        can_add = True
                    else: 
                        # maybe it's a squad
                        if squad.db_group == group:
                            can_add = True

        if can_add:
            squad = self.find_squad(caller, squad_name)
            if not squad:
                caller.msg("Squad not found in your group.")
                return
            char.db.squads.append(squad_name)
            char.db.squads.append(rank_num)
            squad.db_members.append(char)
            caller.msg(f"Added character {char} to squad {squad_name} with rank {rank_num}.")
            return
        else:
            caller.msg("You don't have the right permissions to do this.")
            return


class CmdXWho(Command):

    """
    Full Who By Group
    
    Usage:
      xwho

    Lists logged in characters by group.

    """
    
    key = "xwho"
    help_category = "Roster"

    def func(self):
        
        self.caller.msg("Get Character List by Group")



class CmdShowGroups(MuxCommand):
    """
    To see all available groups or squads in a group.

    Usage:
      +groups
      +group <name>
      +group/info <name>
      +groups/me
      +group/squad <group>/<name>
      +teams

    +groups with no other arguments lists all groups.
    +groups/me lists the groups of which you are a member.

    +group <name> will only function on groups of which you are a member.
    
    This will list insider info about the group such as radio frequencies and 
    message of the day.

    If a group has squads, +group <name> will list those squads. If a group 
    does not have squads (smaller groups) +group <name> will list members.

    To see members of a squad in larger groups, use +group/squad group/name
    Example: +group/squad Robot Masters/Beta

    +group/info on the other hand lists basic information about a group and
    is useful if you need a help file explaining the purpose of a group. 
    It is available for all groups.

    +teams is an alias of +group. It has the same functionality, for those
    used to typing +teams from the old version of the game.

    """
    
    key = "+groups"
    aliases = ["teams", "+teams", "group", "+group", "groups"]
    help_category = "Roster"


    def func(self):
        "This performs the actual command"
        caller = self.caller
        switches = self.switches
        args = self.args

        if not switches:
            if not self.args:
                groups = PlayerGroup.objects.all()
                msg = "List of all Groups:\n"
                for group in groups:
                    msg = msg + group.db_name + " "
                caller.msg(msg)
                return
            else:
                # was the argument a group?
                # was it a group I'm a member of?
                group = self.args
                caller.msg("Group: "+ group)

                return
        if "info" in switches:
            if not self.args:
                caller.msg("Get info for which group?")
                return
            else:
                group = get_group(caller, args)
                text = (f"|{group.db_color}{group.db_name}|n \n Leader: {group.db_leader}  Second: {group.db_twoic} \n {group.db_description}")
                caller.msg(text)
                return
        if "me" in switches:
            text = (f"My groups: {caller.db.pcgroups}")
            caller.msg(text)
            return
        if "squad" in switches:
            errmsg = "Syntax: +group/squad <group>/<name>"
            if not self.args:                
                caller.msg(errmsg)
                return
            elif not "/" in self.args:
                caller.msg(errmsg)
                return
            else:
                group, squad = [part.strip() for part in self.args.rsplit("/", 1)]
                caller.msg("Group: " + group + " Squad: " + squad)
                #just a test of parsing complex command, do database query later
                return


class CmdFCList(MuxCommand):

    """
    Get a list of feature characters.

    Usage:
      +fclist, +cast, +roster
      +fclist/game <game>                                             
      +fclist/group <group>
      +fclist/avail                                     
                                                                              
    The +fclist command will list all the various games that are included 
    in our theme and the created FCs (feature characters) from that game. The   
    +fclist/game <Game> will pull up the specific FCs from that game while 
    +fclist/group <Group> will pull up the various game FCs that are part of that 
    group.    
    (Ex. +fclist/game Megaman X4, +fclist/group Repliforce)

    +cast and +roster are aliases for +fclist.

    """
    
    key = "fclist"
    aliases = ["+fclist","+roster","roster", "cast", "+cast"]
    help_category = "Roster"

    def func(self):
        
        switches = self.switches
        caller = self.caller
        args = self.args
        
        if not switches:
                #TODO - nicer formatting
                msg = "List of all games: \n"
                game_list = GameRoster.objects.all()
                for game in game_list:
                    msg = msg + game.db_name + " "
                caller.msg(msg)
                return
        elif "game" in switches:
            if not args:
                caller.msg("From which game? See fclist (no args) for a list.")
                return
            else:
                try:
                    # maybe this should be iexact, check it later
                    game = GameRoster.objects.filter(db_name__icontains=args)[0]
                except:
                    caller.msg("Game roster missing. Contact an admin.")
                    return
                msg = "--------------------------------------------------------------------------\n"
                msg += (f"List of FCs from {game.db_name}: \n\n")
                roster = game.db_members.all()
                for char in roster:
                    msg += (f"{char.name}: {char.db.appstatus} \n") 
                msg += "--------------------------------------------------------------------------\n"
                caller.msg(msg)
                return

        elif "group" in switches:
            if not args:
                caller.msg("From which group? See help groups for a list.")
                return
            else:
                group = get_group(caller,args)
                if not group:
                    caller.msg("That group was not found.")
                    return
                msg = "--------------------------------------------------------------------------\n"
                msg += (f"List of FCs from {group.db_name}: \n\n")
                roster = group.db_members.all()
                for char in roster:
                    msg += (f"{char.name}: {char.db.appstatus} \n") 
                msg += "--------------------------------------------------------------------------\n"
                caller.msg(msg)
                return

        else: 
            caller.msg("Invalid switch. See help +fclist.")
            return
    

class CmdCreateGroup(MuxCommand):

    """
    Admin side command to create a new PC group.

    Usage:
      makegroup <name>=<leader>
      makegroup/desc <name>=<desc>
      makegroup/2ic <name>=<character>
      makegroup/color <name>=<color code>
      
    Makegroup will make a group with the suggested name, assigning the
    selected person as the leader. A leader is required for any new group.

    The additional command makegroup/desc will change the description for
    the specified group.

    makegroup/2ic will select a character to be the second-in-command of the 
    specified group. Having a second in command is optional.

    Group colors will be used for channels, etc. Use a valid color code.

    """
    
    key = "makegroup"
    aliases = ["+makegroup"]
    help_category = "Roster"
    locks = "perm(Builder)"


    def func(self):

        caller = self.caller
        switches = self.switches
        errmsg = "Syntax error. Please check help makegroup."

        if not switches:
            try:
                char_string = self.rhs
                group_name = self.lhs
            except:
                caller.msg(errmsg)
                return
            leader = self.caller.search(char_string, global_search=True)

            #make sure this is a valid player!
            if not leader:
                self.caller.msg("Character not found.")
                return
            if not inherits_from(leader, settings.BASE_CHARACTER_TYPECLASS):
                self.caller.msg("Character not found.")
                return  
            description = "Starter group description. Ask your admin to change this!"
            group = PlayerGroup.objects.create(db_name=group_name, db_leader = leader, db_description = description)
            
            if group:
                caller.msg(f"Created the new group {group_name} lead by {leader.name}.")
                group.db_members.add(leader)
                leader.msg(f"You were just set leader of a new group: {group.db_name}.")
                return
            else:
                caller.msg("Sorry, an error occured.")
                return
        elif "desc" in switches:
            desc = self.rhs
            group_name = self.lhs
            group = get_group(caller,group_name)
            if group:
                group.db_description = desc
                group.save()
                caller.msg(f"Description for group {group_name}: \n {desc}")
                return
            else:
                caller.msg("Group not found.")
        elif "color" in switches:
            #Make sure this is a valid color

            color = self.rhs
            group_name = self.lhs
            if color_check(color) == "invalid":
                caller.msg("Please use a valid color code.")
                return
            group = get_group(caller,group_name)
            if group:
                group.db_color = color
                group.save()
                caller.msg(f"Color for group |{color}{group_name}|n is set.")
                return
            else:
                caller.msg("Group not found.")
            
        elif "2ic" in switches:
            try:
                char_string = self.rhs
                char = self.caller.search(char_string, global_search=True)

                #make sure this is a valid player!
                if not char:
                    self.caller.msg("Character not found.")
                    return
                if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                    self.caller.msg("Character not found.")
                    return    
                group_name = self.lhs
                group = get_group(caller,group_name)
                group.db_twoic = char
                group.save()
                caller.msg(f"Set {char.name} as second in command to the group {group_name}.")
                return
            except:
                caller.msg(errmsg)
                return

        else:
            caller.msg("Invalid switch. See help makegroup.")
            return

class CmdCreateGameRoster(MuxCommand):

    """
    Admin side command to create a new "Game" which will hold FCs in the 
    roster.

    Usage:
      makegame <name>
      makegame/add <game>=<character>
      
    Should be self-explanitory. This is only for FCs. This does not 
    necessarily match data on the FC's +finger, which will contain
    the most obvious game. 
    
    It is possible to add an FC to multiple games.

    """
    
    key = "makegame"
    aliases = ["+makegame"]
    help_category = "Roster"
    locks = "perm(Builder)"


    def func(self):

        caller = self.caller
        switches = self.switches
        args = self.args
        errmsg = "Syntax error. Please check help makegame."

        if not switches:
            name = args
            try:
                game_roster = GameRoster.objects.create(db_name = name)
                if game_roster:
                    caller.msg(f"Game roster {name} was created.")
                else:
                    caller.msg("Some error occured. No roster created.")
            except:
                caller.msg(errmsg)
                return

        elif "add" in switches:
            char_string = self.rhs
            game_string = self.lhs
            if not char_string:
                caller.msg(errmsg)
                return
            char = caller.search(char_string, global_search=True) 
            if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                caller.msg("Character not found.")
                return
            #many games are similiar, require exact match.
            gamelist = GameRoster.objects.filter(db_name__iexact=game_string)
            game = gamelist[0]
            if game:
                game.db_members.add(char)
                caller.msg(f"Added {char} to game roster {game.db_name}")
                return
            else:
                caller.msg("Game not found.")
                return

        else:
            caller.msg("Invalid switch. See help makegroup.")
            return
