"""
commands related to groups and rosters

These commands do not work at all. They are not even hooked into the model yet. 

"""

from evennia import CmdSet
from evennia import Command
from evennia.commands.default.muxcommand import MuxCommand
from world.pcgroups.models import Squad, PlayerGroup
from world.roster.models import Roster


def get_group(caller, name):
    groups = PlayerGroup.objects.filter(db_name__icontains=name)
    if len.groups > 1:
        caller.msg("Multiple matches. Check the group name or contact admin.")
        return 0
    else:
        return groups[0]


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

    def groupadd(caller, char, name):        
        #choosing first match
        group = get_group(caller, name)
        if group:
            char.db.groups.append(group)
            caller.msg(f"Added {char} to the group {group.db_name}.")
            char.msg(f"You were added to the group {group.db_name}.")
            return
        else:
            caller.msg("Error occured. Check the group name or contact admin.")
            return

    def func(self):
        
        caller = self.caller
        errmsg = "Syntax error - check help addgroup"

        try:
            group = self.rhs
            char = self.lhs
        except ValueError:
            caller.msg(errmsg)
            return
        callergroups = caller.db.groups
        my_group = get_group(caller,group)
        # am I admin?
        if caller.check_permstring("builders"):
            self.groupadd(caller, char, group)
            return
        # am I in that group?
        else:
            for group in callergroups:
                if group == my_group:
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

    If there are no squads in your group, this command will add every character
    in your group to the new squad.
    
    If there is at least one squad, this command will not add any characters
    to the new squad.

    """
    
    key = "+addsquad"
    aliases = ["addsquad"]
    help_category = "Roster"

    def func(self):
        "This performs the actual command"
        errmsg = "What text?"
        if not self.args:
            self.caller.msg(errmsg)
            return
            #todo - parse with the equals
        try:
            text = self.args
            # am I admin?

            # am I a leader? 
            
            # ...of the group I specified?

            # you can't name a squad the same thing as a group, or bad things happen
        except ValueError:
            self.caller.msg(errmsg)
            return
        self.caller.db.quote = text
        self.caller.msg("Add the squad to the group: %s" % text)

# to do above, make it a proper list you can add to

class CmdSetRank(MuxCommand):
    """
    Set the rank of a character.

    Usage:
      +rank <character>=<group or squad>/<number>
      ex:
      +rank Metal Man=Robot Masters/5
      +rank Metal Man=Beta/5

    This command is only used in groups which have a rank and squad setup.

    At this time, groups that are too small to have squads do not have ranks.
    Setting ranks is entirely optional.

    """
    
    key = "+rank"
    aliases = ["rank", "setrank","+setrank"]
    help_category = "Roster"

    def func(self):
        "This performs the actual command"
        errmsg = "What text?"
        if not self.args:
            self.caller.msg(errmsg)
            return
            #todo - parse with the equals
        try:
            text = self.args
            # am I admin?

            # am I a leader? 
            
            # ...of the group I specified?
        except ValueError:
            self.caller.msg(errmsg)
            return
        self.caller.db.quote = text
        self.caller.msg("Add the rank: %s" % text)


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
                msg = "List of all Groups:"
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
                group = get_group(args)
                text = (f"{group.db_name} \n Leader: {group.db_leader}  Second: {group.db_twoic} \n {group.db_description}")
                caller.msg(text)
                return
        if "me" in switches:
            text = (f"My groups: {caller.db.groups}")
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



"""
Syntax: who, +who                                                             
        who<Name, Letters>                                                    
        who <Faction>                                                         


        The 'who' command lists everyone online, their alias, the abbreviaton 
of the faction they're a part of, idle time, connect time, and function.      
        The who<Letters> will display only those online with the letters      
given; such as 'whot' would display everyone whose name starts with T.        
        The who <Faction> command will list only those on within that faction.
(Ex. who R, who W)        

"""


class CmdWho(MuxCommand):
    """
    list who is currently online
    Usage:
      who
      doing
      where
    Shows who is currently online. Doing is an alias that limits info
    also for those with all permissions. Modified to allow players to see
    the locations of other players and add a "where" alias.
    """

    key = "who"
    aliases = ["doing", "where"]
    locks = "cmd:all()"

    # this is used by the parent
    account_caller = True
    help_category = "General"

    # Here we have modified "who" to display the locations of players to other players
    # and to add "where" as an alias.
    def func(self):
        """
        Get all connected accounts by polling session.
        """

        account = self.account
        all_sessions = SESSIONS.get_sessions()

        all_sessions = sorted(all_sessions, key=lambda o: o.account.key) # sort sessions by account name
        pruned_sessions = prune_sessions(all_sessions)

        # check if users are admins and should be able to see all users' session data
        if self.cmdstring == "doing":
            show_session_data = False
        else:
           show_session_data = account.check_permstring("Developer") or account.check_permstring(
               "Admins"
           )

        naccounts = SESSIONS.account_count()
        if show_session_data:
            # privileged info
            table = self.styled_table(
                "|wAccount Name",
                "|wOn for",
                "|wIdle",
                "|wPuppeting",
                "|wRoom",
                "|wCmds",
                "|wProtocol",
                "|wHost",
            )
            for session in all_sessions:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                session_account = session.get_account()
                puppet = session.get_puppet()
                location = puppet.location.key if puppet and puppet.location else "None"
                table.add_row(
                    utils.crop(session_account.get_display_name(account), width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(puppet.get_display_name(account) if puppet else "None", width=25),
                    utils.crop(location, width=35),
                    session.cmd_total,
                    session.protocol_key,
                    isinstance(session.address, tuple) and session.address[0] or session.address,
                )
        else:
            # unprivileged
            table = self.styled_table("|wAccount name", "|wOn for", "|wIdle", "|wRoom")
            for session in pruned_sessions:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                session_account = session.get_account()
                puppet = session.get_puppet()
                location = puppet.location.key if puppet and puppet.location else "None"
                table.add_row(
                    utils.crop(session_account.get_display_name(account), width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(location, width=35),
                )
        is_one = naccounts == 1
        self.msg(
            "|wAccounts:|n\n%s\n%s unique account%s logged in."
            % (table, "One" if is_one else naccounts, "" if is_one else "s")
        )

class CmdFCList(MuxCommand):

    """
    Get a list of feature characters.

    Usage:
      +fclist

    """
    
    key = "+fclist"
    aliases = ["fclist","+roster","roster"]
    help_category = "Roster"

    def func(self):
        
        self.caller.msg("In the future this will list of available and unavailable characters.")
        return
    

class CmdCreateGroup(MuxCommand):

    """
    Admin side command to create a new PC group.

    Usage:
      makegroup <name>

    """
    
    key = "makegroup"
    aliases = ["+makegroup"]
    help_category = "Roster"
    locks = "perm(Builder)"

    def func(self):
        args = self.args
        
        self.caller.msg(f"Created the new group {args}.")
        return