'''
Some random global commands
'''
from evennia import CmdSet
from six import string_types
from commands.command import BaseCommand, Command
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi, color_check
from evennia.accounts.models import AccountDB
from commands.cmdsets import places
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import evtable, utils
import time
from server.utils import time_now
from datetime import datetime, timezone, timedelta


def prune_sessions(session_list):
    # This function modifies the display of "who" and "+pot" so that, if the same player is connected from multiple
    # devices, their character name is only displayed once to avoid confusion. Admin still see all connected sessions.
    session_accounts = [session.account.key for session in session_list]  # get a list of just the names

    unique_accounts = set(session_accounts)
    positions = []

    for acct in unique_accounts:
        # finds positions of account name matches in the session_accounts list
        account_positions = [i for i, x in enumerate(session_accounts) if x == acct]

        # add the position of the account entry we want to the positions list
        if len(account_positions) != 1:
            positions.append(account_positions[-1])
        else:
            positions.append(account_positions[0])

    positions.sort()  # since set() unorders the initial list and we want to keep a specific printed order
    pruned_sessions = []

    for pos in positions:
        pruned_sessions.append(session_list[pos])

    return pruned_sessions


#allwho. This is for admin to see sessions and IPs, which we usually don't care about, but might sometimes.


class CmdAWho(MuxCommand):
    """
    list who is currently online and IP address and details

    Usage:
      awho
      allwho
      
    If you are staff, you might want this more advanced version of 
    'who' that shows more information.
    """

    key = "awho"
    aliases = ["allwho"]
    locks = "perm(Builder))"

    # this is used by the parent
    account_caller = True

    # Here we have modified "who" to display the locations of players to other players
    # and to add "where" as an alias.
    # This version shows players, not accounts
    # removing protocol because I don't really care

    def func(self):
        """
        Get all connected accounts by polling session.
        """

        account = self.account
        all_sessions = SESSIONS.get_sessions()

        all_sessions = sorted(all_sessions, key=lambda o: o.account.key) # sort sessions by account name
        pruned_sessions = prune_sessions(all_sessions)

        # check if users are admins and should be able to see all users' session data

        # to-do: what if I'm not logged in, use Guest permissions
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
                "|wName",
                "|wOn for",
                "|wIdle",
                "|wPlayer",
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
                charname = "|c" + puppet.get_display_name(account) + "|n"
                table.add_row(
                    utils.crop(charname if puppet else "OOC-Idle", width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(session_account.get_display_name(account), width=25),
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
                charname = "|c" + puppet.get_display_name(account) + "|n"
                table.add_row(
                    utils.crop(charname if puppet else "OOC-Idle", width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(location, width=35),
                )
        is_one = naccounts == 1
        self.msg(
            "|wWho's On:|n\n%s\n%s unique account%s logged in."
            % (table, "One" if is_one else naccounts, "" if is_one else "s")
        )

#who from SCS. for now, this also is aliased to 'where', but that will change later.

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

    # Here we have modified "who" to display the locations of players to other players
    # and to add "where" as an alias.
    # This version shows players, not accounts
    # removing protocol because I don't really care

    def func(self):
        """
        Get all connected accounts by polling session.
        """

        account = self.account
        all_sessions = SESSIONS.get_sessions()

        all_sessions = sorted(all_sessions, key=lambda o: o.account.key) # sort sessions by account name
        pruned_sessions = prune_sessions(all_sessions)

        # check if users are admins and should be able to see all users' session data

        # to-do: what if I'm not logged in, use Guest permissions
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
                "|wName",
                "|wOn for",
                "|wIdle",
                "|wPlayer",
                "|wRoom",
            )
            for session in all_sessions:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                session_account = session.get_account()
                puppet = session.get_puppet()
                location = puppet.location.key if puppet and puppet.location else "None"
                charname = "|c" + puppet.get_display_name(account) + "|n"
                table.add_row(
                    utils.crop(charname if puppet else "|cOOC-Idle|n", width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(session_account.get_display_name(account), width=25),
                    utils.crop(location, width=35)
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
                charname = "|c" + puppet.get_display_name(account) + "|n"
                table.add_row(
                    utils.crop(charname if puppet else "OOC-Idle", width=25),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    utils.crop(location, width=35),
                )
        is_one = naccounts == 1
        self.msg(
            "|wWho's On:|n\n%s\n%s unique account%s logged in."
            % (table, "One" if is_one else naccounts, "" if is_one else "s")
        )


class CmdWall(MuxCommand):
    """
    @wall

    Usage:
      @wall <message>

    Shouts a message to all connected players.
    This command should be used to send OOC broadcasts,
    while @gemit is used for IC global messages.
    """

    key = "@wall"
    locks = "cmd:perm(wall) or perm(Wizards)"
    help_category = "Admin"

    def func(self):
        """Implements command"""
        if not self.args:
            self.msg("Usage: @wall <message>")
            return
        message = '%s shouts "%s"' % (self.caller.name, self.args)
        self.msg("Announcing to all connected players ...")
        SESSIONS.announce_all(message)

#this is force from arx, but removing the part where it informs a staff channel about it.
#should be an admin only command. But future puppeting may need this permission.

class CmdForce(MuxCommand):
    """
    @force

    Usage:
      @force <character>=<command>
      @force/char <player>=command

    Forces a given character to execute a command. Without the char switch,
    this will search for character objects in your room, which may be npcs
    that have no player object. With the /char switch, this searches for
    the character of a given player name, who may be anywhere.
    """

    key = "@force"
    locks = "cmd:perm(force) or perm(Wizards)"
    help_category = "GMing"

    def func(self):
        """Implements command"""
        caller = self.caller
        if not self.lhs or not self.rhs:
            self.msg("Usage: @force <character>=<command>")
            return
        if "char" in self.switches:
            player = self.caller.player.search(self.lhs)
            if not player:
                return
            char = player.char_ob
        else:
            char = caller.search(self.lhs)
        if not char:
            caller.msg("No character found.")
            return
        if not char.access(caller, "edit"):
            caller.msg("You don't have 'edit' permission for %s." % char)
            return
        char.execute_cmd(self.rhs)
        caller.msg("Forced %s to execute the command '%s'." % (char, self.rhs))

'''
this is staff list command from arx
todo: fix to list all staff 
'''


class CmdListStaff(MuxCommand):
    """
    
    Usage:
        staff
        staff/all
        staff/list
    
    staff lists staff currently online.
    staff/all or staff/list lists all staff and their status.
    """

    key = "staff"
    aliases = "+staff"

    locks = "cmd:all()"
    help_category = "Admin"

    def func(self):
        """Implements command"""
        caller = self.caller
        staff = AccountDB.objects.filter(db_is_connected=True, is_staff=True)
        table = evtable.EvTable("{wName{n", "{wRole{n", "{wIdle{n", width=78)
        
        if "all" or "list" in self.switches:
            for ob in staff:
                if ob.tags.get("hidden_staff") or ob.db.hide_from_watch:
                    continue
                timestr = CmdWho.get_idlestr(ob.idle_time)
                obname = CmdWho.format_pname(ob)
                table.add_row(obname, ob.db.staff_role or "", timestr)
            caller.msg("{wStaff:{n\n%s" % table)
        else:
            for ob in staff:
                if ob.tags.get("hidden_staff") or ob.db.hide_from_watch:
                    continue
                timestr = CmdWho.get_idlestr(ob.idle_time)
                obname = CmdWho.format_pname(ob)
                table.add_row(obname, ob.db.staff_role or "", timestr)
            caller.msg("{wOnline staff:{n\n%s" % table)

'''
class CmdXWho(MuxCommand):
    """
    xwho
    Usage:
        xwho
    Factional Who.
    Implimentation on hold until we know what groups are, just making a note of it.
    """

'''


class CmdICTime(Command):

    """
    Display the time in-game.
    This displays the in-game time in the IC universe in several IC time zones.

    Syntax:
        ictime
        gametime

    """

    key = "ictime"
    aliases= "+ictime", "date", "+date","gametime", "+gametime"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        """Execute the time command."""
        # Get the actual current time
        now = time_now()
        realyear = now.strftime("%Y")
        icyear = int(realyear) + 213

        # functionality is OK, please make prettier later using https://www.evennia.com/docs/0.9.5/api/evennia.utils.evtable.html

        # format the strings for all times
        msg_string = "|430============================= |wIC Time |430=============================|/|w"
        s_time = datetime.now(timezone(timedelta(hours=-8)))
        sanan_time = s_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        n_time = datetime.now(timezone(timedelta(hours=-5)))
        nyc_time = n_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        l_time = datetime.now(timezone.utc)
        london_time = l_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        m_time = datetime.now(timezone(timedelta(hours=3)))
        moscow_time = m_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        t_time = datetime.now(timezone(timedelta(hours=9)))
        tokyo_time = t_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        i_time = datetime.now(timezone(timedelta(hours=9.5)))
        innerp_time = i_time.strftime("%I:%M %p %a %b %d") + " " + str(icyear)
        msg_string = (msg_string + "|/|_|_San Angeles Time: |_|_|_|_|_|_|_|_" + sanan_time + "|_|_|_|_|_|_|_PST" + "|/|_|_New York Time: |_|_|_|_|_|_|_|_|_|_|_" + nyc_time + "|_|_|_|_|_|_|_EST" + "|/|_|_London Time: |_|_|_|_|_|_|_|_|_|_|_|_|_" + london_time + "|_|_|_|_|_|_|_UTC" + "|/|_|_Moscow Time: |_|_|_|_|_|_|_|_|_|_|_|_|_" + moscow_time + "|_|_|_|_|_|_|_MSK" + "|/|_|_Tokyo Time: |_|_|_|_|_|_|_|_|_|_|_|_|_|_" + tokyo_time + "|_|_|_|_|_|_|_JST" + "|/|_|_Innerpeace Time: |_|_|_|_|_|_|_|_|_" + innerp_time + "|_|_|_|_|_|_ACST")
        msg_string = msg_string + "|/|/|430==================================================================="
        
        self.msg(msg_string)


class CmdWarning(MuxCommand):

    """
    Create a warning that something is approaching!

    Usage:
        warning <name>=<second line of text>

    This creates a warning for dramatic purposes. This can be used, for 
    example, to indicate a boss fight is happening. The second line of text
    is flavor text about the boss, and should be kept short.

    """
    key = "warning"
    aliases= "+warning"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        args = self.args
        caller = self.caller
        try:
            boss, flavortext= args.split("=", 1)
            warning = "  |rWARNING!\tWARNING!\tWARNING!\tWARNING!\tWARNING!"
            
            boss = boss.center(72)
            flavortext = flavortext.center(72)
            emit_text = ("\a\n" + warning + "\n\n|r" + boss + "\n\n|w" + flavortext + "\n\n" + warning +"\n")
            self.caller.location.msg_contents(emit_text)
            return
        except:
            caller.msg("Syntax error. +warning <boss>=<second line>")


class CmdHighlight(MuxCommand):
    """
    Highlight a word that shows up in poses.

    Usage:
      highlight
      highlight/add <word>=<color>
      highlight/del <word>

    The first command displays all words and their corresponding color code
    that you have set. To add words, use the +hightlight/add command with a  
    color code (either single letter or 3-digit xterm code). To remove a name,
    use +highlight/del <word> with the word typed exactly as it appears in 
    +highlight. For your color code, please just enter the number or letter,
    with no additional punctuation, eg:

    highlight/add Mega=245

    This command will highlight all occurrences of the given word in any 
    pose that you see within a scene. You can hightlight up to 10 words.

    To see a full list of colors, use either
    color ansi
    color xterm256

    """

    key = "highlight"
    switch_options = ("add", "del")
    aliases = ["+highlight"]

    help_category = "General"


    def func(self):
        caller = self.caller
        args = self.args
        switches = self.switches
        high_list = caller.db.highlightlist
        
        #todo - add quota

        errmsg = "Syntax error, see help highlight"
        if not args and not switches:
            if not high_list:
                caller.msg("No highlighted words found.")
                return
            else:
                msg_string = ("Highlighted words:\n")
                for word, color in high_list:
                    msg_string = msg_string +  "Word: |" + color + word + "|n Color: |" + color  + color + "|n\n"
                caller.msg(msg_string)
                return

        if "add" in switches:
            if not args:
                caller.msg(errmsg)
                return
            if not high_list:
                caller.db.highlightlist = []

            high_str = args.split("=")
            if len(high_str) == 1:
                caller.msg("Syntax error, did you forget =?")
                return

            if color_check(high_str[1]) == "invalid":
                caller.msg("Please use a valid color code.")
                return
            else:
                high_list.append(high_str)
                caller.msg(f"Added word |{high_str[1]}{high_str[0]}|n.")
                return


        if "del" in switches:
            if not args:
                caller.msg(errmsg)
                return
            else:
                matched = False
                check = 0
                for word, color in high_list:
                    if word == args:
                        matched = True                        
                        caller.msg(f"Deleted word pairing {high_list[check]}|n.")
                        del high_list[check:check+1]
                        check = check +1
                        return
                if not matched:
                    caller.msg(f"{args} was not found.")
                    return




