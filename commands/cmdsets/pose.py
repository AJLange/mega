"""
Pose-related and pose formatting commands will go in this file.

"""
from evennia import CmdSet
from six import string_types
from commands.command import BaseCommand
from evennia.commands.default.muxcommand import MuxCommand, MuxAccountCommand
from server.utils import sub_old_ansi, highlight_words
from evennia.utils import utils, evtable
from evennia.commands.default.general import CmdSay
from evennia.commands.default.account import CmdOOC
from commands.cmdsets import places
#from commands.cmdsets import scenes
from evennia.comms.models import TempMsg
from evennia.server.sessionhandler import SESSIONS
from evennia.utils.utils import inherits_from
from django.conf import settings

    

def append_stage(self, stage, pose):
    
    if not stage:
        return False
    else:
        #append my stage to the pose and return it
        prefix = (f"From {stage}, \n")
        pose = prefix + pose
        return pose


class CmdThink(BaseCommand):
    """
    This is just for thinking out loud.
    """
    key = "think"
    lock = "cmd:all()"
    help_category = "General"

    def func(self):
        "This performs the actual command"
        errmsg = "You can't think of anything."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            message = self.args
            message = sub_old_ansi(message)
            message = highlight_words(message, self.caller)
            self.caller.msg(f"You think:{str(message)}")
        except ValueError:
            self.caller.msg(errmsg)
            return
        
'''
Emit is basic and uncapped and unlocked and will require more locks
at a later time to do things like nospoof. Just making it work for
right now.

'''

class CmdOOCSay(MuxCommand):
    """
    ooc

    Usage:
      ooc <message>

    Send an OOC message to your current location. For IC messages,
    use 'say' instead.
    """

    key = "ooc"
    locks = "cmd:all()"
    help_category = "Comms"

    def func(self):
        """Run the OOCsay command"""

        caller = self.caller
        speech = self.raw.lstrip()

        if not speech:
            caller.msg(
                "No message specified. If you wish to stop being IC, use @ooc instead."
            )
            return

        oocpose = False
        nospace = False
        if speech.startswith(";") or speech.startswith(":"):
            oocpose = True
            if speech.startswith(";"):
                nospace = True
            speech = speech[1:]

        # calling the speech hook on the location
        speech = caller.location.at_say(speech)
        options = {"ooc_note": True, "log_msg": True}

        # Feedback for the object doing the talking.
        if not oocpose:
            caller.msg("(OOC) You say: %s" % speech)

            # Build the string to emit to neighbors.
            emit_string = "(OOC) %s says: %s" % (caller.name, speech)
            caller.location.msg_contents(emit_string, from_obj=caller, exclude=caller, options=options)
        else:
            if nospace:
                emit_string = "(OOC) %s %s" % (caller.name, speech)
            else:
                emit_string = "(OOC) %s %s" % (caller.name, speech)
            caller.location.msg_contents(emit_string, exclude=None, options=options, from_obj=caller)


class CmdEmit(MuxCommand):
    """
    @emit

    Usage:
      @emit <message>

    Emits a message to your immediate surroundings. Allows for the most flexible
    structure of posing.
    
    This message will not necessarily contain your character's name, unless the 
    other players in the room have nospoof set. It's polite to indicate the name
    of your character somewhere in the pose, for clarity!

    """

    key = "@emit"
    aliases = ["emit", "\\\\"]
    locks = "cmd:all()"
    help_category = "Social"
    arg_regex = None
    perm_for_switches = "Builders"

    
    def func(self):
        """Implement the command"""

        caller = self.caller
        if caller.check_permstring(self.perm_for_switches):
            args = self.args
        else:
            args = self.raw.lstrip(" ")

        if not args:
            string = "Usage: "
            string += "\n@emit <message>"
            caller.msg(string)
            return

        perm = self.perm_for_switches
        normal_emit = False
        has_perms = caller.check_permstring(perm)

        # we check which command was used to force the switches
        cmdstring = self.cmdstring.lstrip("@").lstrip("+")

        if cmdstring == "pemit":
            if not caller.check_permstring("builders"):
                caller.msg("Only staff can use this command.")
                return
            players_only = True

        if not caller.check_permstring(perm):
            rooms_only = False
            players_only = False

        if not self.rhs or not has_perms:
            message = args
            normal_emit = True
            objnames = []
            do_global = False
        else:
            do_global = True
            message = self.rhs
            if caller.check_permstring(perm):
                objnames = self.lhslist
            else:
                objnames = [x.key for x in caller.location.contents if x.player]
        if do_global:
            do_global = has_perms


        # normal emits by players are just sent to the room
        # right now this does not do anything with nospoof. add later in 
        # POT functionality.

        if normal_emit:
            try:
                message = self.args
                message = sub_old_ansi(message)
                in_stage = caller.db.in_stage
                if in_stage:
                    message = append_stage(message)
                self.caller.location.msg_contents(message, from_obj=caller)
            except ValueError:
                self.caller.msg("")
                return
        
            return


class CmdPEmit(MuxCommand):
    """
    @pemit

    Usage:
      @pemit [<obj>, <obj>, ... =] <message>

   
    @pemit is an emit directly to another player or player list. 
    This emit is not visible to other players, even in the same room as
    the targetted player.
    For now, this power is limited only to staffers.

    """

    key = "@pemit"
    aliases = ["pemit"]
    locks = "cmd:all()"
    help_category = "Social"
    arg_regex = None
    perm_for_switches = "Builders"
    success_emit = False

    def get_help(self, caller, cmdset):
        """Returns custom help file based on caller"""
        if caller.check_permstring(self.perm_for_switches):
            return self.__doc__
        help_string = """
        @emit

        Usage :
            @emit <message>

        Emits a message to your immediate surroundings. This command is
        used to provide more flexibility than the structure of poses, but
        please remember to indicate your character's name.
        """
        return help_string

    def func(self):
        """Implement the command"""

        caller = self.caller
        if caller.check_permstring(self.perm_for_switches):
            args = self.args
        else:
            args = self.raw.lstrip(" ")

        if not args:
            string = "Usage: "
            string += "\n@pemit  [<obj>, <obj>, ... =] <message>"
            caller.msg(string)
            return

        perm = self.perm_for_switches
        normal_emit = False
        has_perms = caller.check_permstring(perm)

        # we check which command was used to force the switches
        cmdstring = self.cmdstring.lstrip("@").lstrip("+")

        if cmdstring == "pemit":
            if not caller.check_permstring("builders"):
                caller.msg("Only staff can use this command.")
                return
            if not args:
                string = "@pemit to who?"
                caller.msg(string)
                return
            largs = args.split('=')
            if len(largs) <= 1:
                caller.msg("Emit what message?")
                return
            message = largs[1]
            message = sub_old_ansi(message)
            target_all = largs[0]
            target_list = target_all.split(',')
            for player in target_list:
                player = player.strip()
                # find a matching player (anywhere)
                char = caller.search(player, global_search=True) 
                if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                        self.caller.msg("Character %s was not found." % player)
                else:
                    char.msg(message)
                    success_emit = True
                    caller.msg("Pemitted to: %s:" % char)
            if not success_emit:
                caller.msg("No message sent.")
                return
            # successfully did emit, so mirror message to myself.
            caller.msg(message)
            return                


        if not self.rhs or not has_perms:
            message = args
            normal_emit = True
            objnames = []
            do_global = False
        else:
            do_global = True
            message = self.rhs
            if caller.check_permstring(perm):
                objnames = self.lhslist
            else:
                objnames = [x.key for x in caller.location.contents if x.player]
        if do_global:
            do_global = has_perms


        # normal emits by players are just sent to the room
        # right now this does not do anything with nospoof. add later in 
        # POT functionality.

        if normal_emit:
            try:
                message = self.args
                message = sub_old_ansi(message)
                in_stage = caller.db.in_stage
                if in_stage:
                    message = append_stage(message)
                self.caller.location.msg_contents(message, from_obj=caller)
            except ValueError:
                self.caller.msg("")
                return
        
            return
            

class CmdPose(BaseCommand):
    """
    pose - strike a pose

    Usage:
      pose <pose text>
      pose's <pose text>

    Describe an action being taken. The pose text will
    automatically begin with your name. Following pose with an apostrophe,
    comma, or colon will not put a space between your name and the character.
    Ex: 'pose, text' is 'Yourname, text'. Similarly, using the ; alias will
    not append a space after your name. Ex: ';'s adverb' is 'Name's adverb'.

    """

    key = "pose"
    aliases = [":", "emote", ";"]
    locks = "cmd:all()"
    help_category = "Social"
    arg_regex = None

    # noinspection PyAttributeOutsideInit
    def parse(self):
        """
        Custom parse the cases where the emote
        starts with some special letter, such
        as 's, at which we don't want to separate
        the caller's name and the emote with a
        space.
        """
        super(CmdPose, self).parse()
        args = self.args
        if (args and not args[0] in ["'", ",", ":"]) and not self.cmdstring.startswith(
            ";"
        ):
            args = " %s" % args.lstrip(" ")
        self.args = args

    def func(self):

        "This performs the actual command"
        errmsg = "Pose what?"
        caller = self.caller
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            message = self.args
            message = sub_old_ansi(message)
            in_stage = caller.db.in_stage
            # this won't work actually, but fix later
            if in_stage:
                message = append_stage(message)
            caller.location.msg_action(caller, message)
        except ValueError:
            self.caller.msg(errmsg)
            return
        

class CmdSay(MuxCommand):
    """
    speak as your character
    Usage:
      say <message>
    Talk to those in your current location.
    """

    key = "say"
    aliases = ['"', "'"]
    locks = "cmd:all()"

    # Here we overwrite the default "say" command so that it updates the pose timer for +pot,
    # as well as for LogEntry, etc.
    def func(self):
        """Run the say command"""

        caller = self.caller

        # Update the pose timer if outside of OOC room
        # This assumes that the character's home is the OOC room, which it is by default
        if caller.location != caller.home:
            #caller.set_pose_time(time.time())
            caller.set_obs_mode(False)

        if not self.args:
            caller.msg("Say what?")
            return

        message = self.args

        # Calling the at_before_say hook on the character
        message = caller.at_before_say(message)
        # tailored_msg(caller, message)
        # TODO: Apply tailored_msg to the first person/third person distinction in say display.

        # If speech is empty, stop here
        if not message:
            return

        # Call the at_after_say hook on the character
        in_stage = caller.db.in_stage
        if in_stage:
            message = append_stage(message)
        caller.at_say(message, msg_self=True)

        # If an event is running in the current room, then write to event log
        #if caller.location.db.active_event:
            #scene = Scene.objects.get(pk=self.caller.location.db.event_id)
            #scene.addLogEntry(LogEntry.EntryType.SAY, self.args, self.caller)
            #add_participant_to_scene(self.caller, scene)


class CmdMegaSay(CmdSay):
    """
    Override of CmdSay

    We don't do other languages, so don't need that functionality
    Eventually over-ride this so autosay won't fire in IC rooms,
    as a treat.
    
    """

    __doc__ = CmdSay.__doc__
    arg_regex = None

    # noinspection PyAttributeOutsideInit
    def parse(self):
        """Make sure cmdstring 'say' has a space, other aliases don't"""
        super(CmdMegaSay, self).parse()
        if self.cmdstring == "say":
            self.args = " %s" % self.args.lstrip()

    def func(self):
        """Replacement for CmdSay's func"""
        if not self.raw:
            self.msg("Say what?")
            return
        options = {"is_pose": True}
        speech = self.raw.lstrip(" ")
        # calling the speech hook on the location
        speech = self.caller.location.at_say(speech)
        # Feedback for the object doing the talking.
        langstring = ""
        
        speech = sub_old_ansi(speech)
        # Build the string to emit to neighbors.
        pre_name_emit_string = ' says%s, "%s"' % (langstring, speech)
        self.caller.location.msg_action(
            self.caller, pre_name_emit_string, options=options
        )


class CmdPage(BaseCommand):
    """
    page - send private message

    Usage:
      page[/switches] [<player>,<player2>,... = <message>]
      page[/switches] [<player> <player2> <player3>...= <message>]
      page [<message to last paged player>]
      tell  <player> <message>
      ttell [<message to last paged player>]
      reply [<message to player who last paged us and other receivers>]
      page/list <number>
      page/noeval
      page/allow <name>
      page/block <name>
      page/reply <message>

    Switch:
      last - shows who you last messaged
      list - show your last <number> of tells/pages (default)

    Send a message to target user (if online), or to the last person
    paged if no player is given. If no argument is given, you will
    get a list of your latest messages. Note that pages are only
    saved for your current session. Sending pages to multiple receivers
    accepts the names either separated by commas or whitespaces.

    /allow toggles whether someone may page you when you use @settings/ic_only.
    /block toggles whether all pages are blocked from someone.
    """

    key = "page"
    aliases = ["tell", "p", "pa", "pag", "ttell", "reply"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Comms"
    arg_regex = r"\/|\s|$"

    def disp_allow(self):
        """Displays those we're allowing"""
        self.msg(
            "{wPeople on allow list:{n %s"
            % ", ".join(str(ob) for ob in self.caller.allow_list)
        )
        self.msg(
            "{wPeople on block list:{n %s"
            % ", ".join(str(ob) for ob in self.caller.block_list)
        )

    def func(self):
        """Implement function using the Msg methods"""

        # this is a ArxPlayerCommand, which means caller will be a Player.
        caller = self.caller
        if "allow" in self.switches or "block" in self.switches:
            if not self.args:
                self.disp_allow()
                return
            targ = caller.search(self.args)
            if not targ:
                return
            if "allow" in self.switches:
                if targ not in caller.allow_list:
                    caller.allow_list.append(targ)
                    # allowing someone removes them from the block list
                    if targ in caller.block_list:
                        caller.block_list.remove(targ)
                else:
                    caller.allow_list.remove(targ)
            if "block" in self.switches:
                if targ not in caller.block_list:
                    caller.block_list.append(targ)
                    # blocking someone removes them from the allow list
                    if targ in caller.allow_list:
                        caller.allow_list.remove(targ)
                else:
                    caller.block_list.remove(targ)
            self.disp_allow()
            return
        # get the messages we've sent (not to channels)
        if not caller.ndb.pages_sent:
            caller.ndb.pages_sent = []
        pages_we_sent = caller.ndb.pages_sent
        # get last messages we've got
        if not caller.ndb.pages_received:
            caller.ndb.pages_received = []
        pages_we_got = caller.ndb.pages_received

        if "last" in self.switches:
            if pages_we_sent:
                recv = ",".join(str(obj) for obj in pages_we_sent[-1].receivers)
                self.msg("You last paged {c%s{n:%s" % (recv, pages_we_sent[-1].message))
                return
            else:
                self.msg("You haven't paged anyone yet.")
                return
        if "list" in self.switches or not self.raw:
            pages = pages_we_sent + pages_we_got
            pages.sort(key=lambda x: x.date_created)

            number = 5
            if self.args:
                try:
                    number = int(self.args)
                except ValueError:
                    self.msg("Usage: tell [<player> = msg]")
                    return

            if len(pages) > number:
                lastpages = pages[-number:]
            else:
                lastpages = pages
            template = "{w%s{n {c%s{n paged to {c%s{n: %s"
            lastpages = "\n ".join(
                template
                % (
                    utils.datetime_format(page.date_created),
                    ",".join(obj.name for obj in page.senders),
                    "{n,{c ".join([obj.name for obj in page.receivers]),
                    page.message,
                )
                for page in lastpages
            )

            if lastpages:
                string = "Your latest pages:\n %s" % lastpages
            else:
                string = "You haven't paged anyone yet."
            self.msg(string)
            return
        # if this is a 'tell' rather than a page, we use different syntax
        cmdstr = self.cmdstring.lower()
        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if cmdstr.startswith("tell"):
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg("The tell format requires both a name and a message.")
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))
        # go through our comma separated list, also separate them by spaces
        elif lhs and rhs:
            tarlist = []
            for ob in lhslist:
                for word in ob.split():
                    tarlist.append(word)
            lhslist = tarlist

        # We are sending. Build a list of targets
        if "reply" in self.switches or cmdstr == "reply":
            if not pages_we_got:
                self.msg("You haven't received any pages.")
                return
            last_page = pages_we_got[-1]
            receivers = set(last_page.senders + last_page.receivers)
            receivers.discard(self.caller)
            rhs = self.args
        elif (not lhs and rhs) or (self.args and not rhs) or cmdstr == "ttell":
            # If there are no targets, then set the targets
            # to the last person we paged.
            # also take format of p <message> for last receiver
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
                # if it's a 'tt' command, they can have '=' in a message body
                if not rhs or cmdstr == "ttell":
                    rhs = self.raw.lstrip()
            else:
                self.msg("Who do you want to page?")
                return
        else:
            receivers = lhslist

        if "noeval" in self.switches:
            rhs = raw(rhs)

        recobjs = []
        for receiver in set(receivers):
            # originally this section had this check, which always was true
            # Not entirely sure what he was trying to check for
            if isinstance(receiver, string_types):
                findpobj = caller.search(receiver)
            else:
                findpobj = receiver
            pobj = None
            if findpobj:
                # Make certain this is a player object, not a character
                if hasattr(findpobj, "character"):
                    # players should always have is_connected, but just in case
                    if not hasattr(findpobj, "is_connected"):
                        # only allow online tells
                        self.msg("%s is not online." % findpobj)
                        continue
                    elif findpobj.character:
                        if (
                            hasattr(findpobj.character, "player")
                            and not findpobj.character.player
                        ):
                            self.msg("%s is not online." % findpobj)
                        else:
                            pobj = findpobj.character
                    elif not findpobj.character:
                        # player is either OOC or offline. Find out which
                        if hasattr(findpobj, "is_connected") and findpobj.is_connected:
                            pobj = findpobj
                        else:
                            self.msg("%s is not online." % findpobj)
                else:
                    # Offline players do not have the character attribute
                    self.msg("%s is not online." % findpobj)
                    continue
                if findpobj in caller.block_list:
                    self.msg(
                        "%s is in your block list and would not be able to reply to your page."
                        % findpobj
                    )
                    continue
                if caller.tags.get("chat_banned") and (
                    caller not in findpobj.allow_list
                    or findpobj not in caller.allow_list
                ):
                    self.msg(
                        "You cannot page if you are not in each other's allow lists."
                    )
                    continue
                if (
                    findpobj.tags.get("ic_only")
                    or caller in findpobj.block_list
                    or findpobj.tags.get("chat_banned")
                ) and not caller.check_permstring("builders"):
                    if caller not in findpobj.allow_list:
                        self.msg("%s is IC only and cannot be sent pages." % findpobj)
                        continue
            else:
                continue
            if pobj:
                if hasattr(pobj, "player") and pobj.player:
                    pobj = pobj.player
                recobjs.append(pobj)

        if not recobjs:
            self.msg("No one found to page.")
            return
        if len(recobjs) > 1:
            rec_names = ", ".join("{c%s{n" % str(ob) for ob in recobjs)
        else:
            rec_names = "{cyou{n"
        header = "{wPlayer{n {c%s{n {wpages %s:{n" % (caller, rec_names)
        message = rhs
        pagepose = False
        # if message begins with a :, we assume it is a 'page-pose'
        if message.startswith(":") or message.startswith(";"):
            pagepose = True
            header = "From afar,"
            if len(recobjs) > 1:
                header = "From afar to %s:" % rec_names
            if message.startswith(":"):
                message = "{c%s{n %s" % (caller, message.strip(":").strip())
            else:
                message = "{c%s{n%s" % (caller, message.strip(";").strip())

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)
        caller.ndb.pages_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        r_strings = []
        for pobj in recobjs:
            if not pobj.access(caller, "msg"):
                r_strings.append("You are not allowed to page %s." % pobj)
                continue
            if "ic_only" in caller.tags.all() and pobj not in caller.allow_list:
                msg = "%s is not in your allow list, and you are IC Only. " % pobj
                msg += "Allow them to send a page, or disable the IC Only @setting."
                self.msg(msg)
                continue
            pobj.msg(
                "%s %s" % (header, message), from_obj=caller, options={"log_msg": True}
            )
            if not pobj.ndb.pages_received:
                pobj.ndb.pages_received = []
            pobj.ndb.pages_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                r_strings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name.capitalize())
            afk = pobj.db.afk
            if afk:
                pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                r_strings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if r_strings:
            self.msg("\n".join(r_strings))
        if received:
            if pagepose:
                self.msg("Long distance to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You paged %s with: '%s'." % (", ".join(received), message))



class CmdPoseColors(MuxCommand):
    """
    Toggle colored names in poses. Posecolors/self and
    posecolors/others are used to set the colors of one's
    own name and other names, respectively. Type "color
    xterm256" to see the list of eligible color codes.
    Usage:
      posecolors on/off
      posecolors/self <xterm256 code>
      posecolors/others <xterm256 code>
    Examples:
      posecolors on
      posecolors/self 555
      posecolors/others 155
    """

    key = "posecolors"
    aliases = "+posecolors"
    switch_options = ("self", "others")
    locks = "cmd:all()"

    def func(self):
        """Changes pose colors"""

        caller = self.caller
        args = self.args
        switches = self.switches

        if switches or args:
            if args == "on":
                caller.db.pose_colors_on = True
                caller.msg("Name highlighting enabled")
            elif args == "off":
                caller.db.pose_colors_on = False
                caller.msg("Name highlighting disabled")
            elif "self" in switches:
                if len(args) == 3 and args.isdigit:
                    caller.db.pose_colors_self = str(args)
                    caller.msg("Player's name highlighting color updated")
            elif "others" in switches:
                if len(args) == 3 and args.isdigit:
                    caller.db.pose_colors_self = str(args)
                    caller.msg("Other's name highlighting color updated")
            else:
                caller.msg("Unknown switch/argument!")
                return

class CmdPage(MuxCommand):
    """
    send a private message to another account
    Usage:
      page[/switches] [<account>,<account>,... = <message>]
      tell        ''
      page <number>
    Switch:
      last - shows who you last messaged
      list - show your last <number> of tells/pages (default)
    Send a message to target user (if online). If no
    argument is given, you will get a list of your latest messages.
    """

    key = "page"
    aliases = ["tell", "p"]
    switch_options = ("last", "list")
    locks = "cmd:not pperm(page_banned)"
    help_category = "Comms"
    # This is a modified version of the page command that notifies recipients of pages
    # when there are multiple recipients, i.e., when you are in a group conversation.
    # By default, Evennia's page command doesn't inform you that multiple people have
    # received a page that you have received, for some very strange reason!

    # this is used by the COMMAND_DEFAULT_CLASS parent
    account_caller = True

    def func(self):
        """Implement function using the Msg methods"""

        # Since account_caller is set above, this will be an Account.
        caller = self.caller

        # get the messages we've sent (not to channels)
        pages_we_sent = Msg.objects.get_messages_by_sender(caller, exclude_channel_messages=True)
        # get last messages we've got
        pages_we_got = Msg.objects.get_messages_by_receiver(caller)

        if "last" in self.switches:
            if pages_we_sent:
                recv = ",".join(obj.key for obj in pages_we_sent[-1].receivers)
                self.msg("You last paged |c%s|n:%s" % (recv, pages_we_sent[-1].message))
                return
            else:
                self.msg("You haven't paged anyone yet.")
                return

        if not self.args or not self.rhs:
            pages = pages_we_sent + pages_we_got
            pages = sorted(pages, key=lambda page: page.date_created)

            number = 5
            if self.args:
                try:
                    number = int(self.args)
                except ValueError:
                    self.msg("Usage: tell [<account> = msg]")
                    return

            if len(pages) > number:
                lastpages = pages[-number:]
            else:
                lastpages = pages
            to_template = "|w{date}{clr} {sender}|nto{clr}{receiver}|n:> {message}"
            from_template = "|w{date}{clr} {receiver}|nfrom{clr}{sender}|n:< {message}"
            listing = []
            prev_selfsend = False
            for page in lastpages:
                multi_send = len(page.senders) > 1
                multi_recv = len(page.receivers) > 1
                sending = self.caller in page.senders
                # self-messages all look like sends, so we assume they always
                # come in close pairs and treat the second of the pair as the recv.
                selfsend = sending and self.caller in page.receivers
                if selfsend:
                    if prev_selfsend:
                        # this is actually a receive of a self-message
                        sending = False
                        prev_selfsend = False
                    else:
                        prev_selfsend = True

                clr = "|c" if sending else "|g"

                sender = f"|n,{clr}".join(obj.key for obj in page.senders)
                receiver = f"|n,{clr}".join([obj.name for obj in page.receivers])
                if sending:
                    template = to_template
                    sender = f"{sender} " if multi_send else ""
                    receiver = f" {receiver}" if multi_recv else f" {receiver}"
                else:
                    template = from_template
                    receiver = f"{receiver} " if multi_recv else ""
                    sender = f" {sender} " if multi_send else f" {sender}"

                listing.append(
                    template.format(
                        date=utils.datetime_format(page.date_created),
                        clr=clr,
                        sender=sender,
                        receiver=receiver,
                        message=page.message,
                    )
                )
            lastpages = "\n ".join(listing)

            if lastpages:
                string = "Your latest pages:\n %s" % lastpages
            else:
                string = "You haven't paged anyone yet."
            self.msg(string)
            return

        # We are sending. Build a list of targets

        if not self.lhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Who do you want to page?")
                return
        else:
            receivers = self.lhslist

        recobjs = []
        for receiver in set(receivers):
            if isinstance(receiver, str):
                pobj = caller.search(receiver)
            elif hasattr(receiver, "character"):
                pobj = receiver
            else:
                self.msg("Who do you want to page?")
                return
            if pobj:
                recobjs.append(pobj)
        if not recobjs:
            self.msg("Noone found to page.")
            return

        header = "|c%s|n |wpages|n" % caller.key # Ivo pages Headwiz, Ugen: <message>
        message = self.rhs

        # if message begins with a :, we assume it is a 'page-pose'
        if message.startswith(":"):
            message = "%s %s" % (caller.key, message.strip(":").strip())

        # create the persistent message object
        create.create_message(caller, message, receivers=recobjs)

        # tell the accounts they got a message.
        received = []
        rstrings = []
        namelist = ""
        for count, pobj in enumerate(recobjs):
            if count == 0:
                namelist += "|c{0}|n".format(pobj.name)
            else:
                namelist += ", |c{0}|n".format(pobj.name)

        for pobj in recobjs:
            if not pobj.access(caller, "msg"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            pobj.msg("%s %s: %s" % (header, namelist, message))
            if hasattr(pobj, "sessions") and not pobj.sessions.count():
                received.append("|C%s|n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("|c%s|n" % pobj.name)
        if rstrings:
            self.msg("\n".join(rstrings))
        self.msg("You paged %s with: '%s'." % (", ".join(received), message))


class CmdAside(MuxCommand):
    """
    
    Usage:
      aside <message>

    Aside functions exactly like @emit, but is used for small side comments not
    intended to be a major pose. 

    The difference between +aside and @emit is that +aside does not trigger
    Pose Order Tracker (see help files for +pot), meaning your turn in 'line'
    is still preserved. Use this for corrections to typos, or small comments
    that slide between poses that your character would make. 

    Please do not use +aside for large substantial poses that take your turn.
    Nothing should be done in an aside that would imply a roll of the
    dice or full action.

    Asides still show up in the autologger for the scene.
    """

    key = "aside"
    aliases = ["+aside"]

    help_category = "Comms"

    def func(self):

        """Implement the command"""

        caller = self.caller
        args = self.raw.lstrip(" ")

        if not args:
            string = "Usage: aside <pose>"
            caller.msg(string)
            return

        # normal emits by players are just sent to the room
        # right now this does not do anything with nospoof. add later in 
        # POT functionality.

        try:
            message = self.args
            message = sub_old_ansi(message)
            in_stage = caller.db.in_stage
            if in_stage:
                message = append_stage(message)
            self.caller.location.msg_contents(message, from_obj=caller)
        except ValueError:
            self.caller.msg("")
            return
        

