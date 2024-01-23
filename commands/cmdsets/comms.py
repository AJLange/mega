"""
Home of mail and radio commands

"""


from evennia import default_cmds
from commands.command import CmdAbilities
from evennia import CmdSet
from commands import command
from commands.base import BaseCommand
from six import string_types
from server.utils import sub_old_ansi
from evennia.server.sessionhandler import SESSIONS
import time
import re
from evennia import ObjectDB, AccountDB
from evennia.comms.models import Msg
from evennia.commands.default.muxcommand import MuxCommand


class CmdWhisper(MuxCommand):
    """
    whisper - send private IC message

    Usage:
      whisper [<player>,<player>,... = <message>]
      whisper =<message> - sends whisper to last person you whispered
      whisper <name> <message>

    Send an IC message to a character in your room. A whisper of the format
    "whisper player=Hello" will send a message in the form of "You whisper
    <player>". A whisper of the format "whisper player=:does an emote" will appear
    in the form of "Discreetly, soandso does an emote" to <player>. 

    Whispering to another player in the room emits to the room a message that 
    a whisper occured between you, but not the message. Whisper accepts
    multiple targets.

    Characters with the enhanced_senses ability can overhear the text of
    whispers.

    """

    key = "whisper"
    aliases = ["+whisper"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Social"
    simplified_key = "mutter"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        # get the messages we've sent (not to channels)
        if not caller.ndb.whispers_sent:
            caller.ndb.whispers_sent = []
        pages_we_sent = caller.ndb.whispers_sent
        # get last messages we've got
        if not caller.ndb.whispers_received:
            caller.ndb.whispers_received = []


        if not self.args:
            self.msg("Usage: whisper [<player> = msg]")
            return

            
        # We are sending. Build a list of targets
        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if not self.rhs:
            # MMO-type whisper. 'whisper <name> <target>'
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg(
                    "The MMO-style whisper format requires both a name and a message."
                )
                caller.msg(
                    "To send a message to your last whispered character, use {wwhisper =<message>"
                )
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))

        if not lhs and rhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Who do you want to whisper?")
                return
        else:
            receivers = lhslist

        #todo, emit that the person whispered to the room.

        recobjs = []
        for receiver in set(receivers):

            if isinstance(receiver, string_types):
                pobj = caller.search(receiver, use_nicks=True)
            elif hasattr(receiver, "character"):
                pobj = receiver.character
            elif hasattr(receiver, "player"):
                pobj = receiver
            else:
                self.msg("Who do you want to whisper?")
                return
            if pobj:
                if hasattr(pobj, "has_account") and not pobj.has_account:
                    self.msg("You may only send whispers to online characters.")
                elif not pobj.location or pobj.location != caller.location:
                    self.msg("You may only whisper characters in the same room as you.")
                else:
                    recobjs.append(pobj)
        if not recobjs:
            self.msg("No one found to whisper.")
            return
        header = "{c%s{n whispers," % caller.name
        message = rhs
        mutter_text = ""
        # if message begins with a :, we assume it is a 'whisper-pose'
        if message.startswith(":"):
            message = "%s {c%s{n %s" % (
                "Discreetly,",
                caller.name,
                message.strip(":").strip(),
            )
            is_a_whisper_pose = True
        elif message.startswith(";"):
            message = "%s {c%s{n%s" % (
                "Discreetly,",
                caller.name,
                message.lstrip(";").strip(),
            )
            is_a_whisper_pose = True
        else:
            is_a_whisper_pose = False
            message = '"' + message + '"'

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)

        caller.ndb.whispers_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        rstrings = []
        for pobj in recobjs:
            otherobs = [ob for ob in recobjs if ob != pobj]
            if not pobj.access(caller, "tell"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            if is_a_whisper_pose:
                omessage = message
                if otherobs:
                    omessage = "(Also sent to %s.) %s" % (
                        ", ".join(ob.name for ob in otherobs),
                        message,
                    )
                pobj.msg(omessage, from_obj=caller, options={"is_pose": True})
            else:
                if otherobs:
                    myheader = header + " to {cyou{n and %s," % ", ".join(
                        "{c%s{n" % ob.name for ob in otherobs
                    )
                else:
                    myheader = header
                pobj.msg(
                    "%s %s" % (myheader, message),
                    from_obj=caller,
                    options={"is_pose": True},
                )
            if not pobj.ndb.whispers_received:
                pobj.ndb.whispers_received = []
            pobj.ndb.whispers_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name)
                # afk = pobj.player_ob and pobj.player_ob.db.afk
                # if afk:
                #     pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                #     rstrings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if rstrings:
            self.msg("\n".join(rstrings))
        if received:
            if is_a_whisper_pose:
                self.msg("You posed to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You whispered to %s, %s" % (", ".join(received), message))
                if "mutter" in self.switches or "mutter" in self.cmdstring:
                    from random import randint

                    word_list = rhs.split()
                    chosen = []
                    num_real = 0
                    for word in word_list:
                        if randint(0, 2):
                            chosen.append(word)
                            num_real += 1
                        else:
                            chosen.append("...")
                    if num_real:
                        mutter_text = " ".join(chosen)
                if mutter_text:
                    emit_string = ' mutters, "%s{n"' % mutter_text
                    exclude = [caller] + recobjs
                    caller.location.msg_action(
                        self.caller,
                        emit_string,
                        options={"is_pose": True},
                        exclude=exclude,
                    )
                    self.mark_command_used()
        caller.posecount += 1


class CmdMutter(MuxCommand):
    """
    Mutter - send private IC message

    Usage:
      mutter [<player>,<player>,... = <message>]
      mutter =<message> - sends mutter to last person you muttered to
      mutter <name> <message>
      mutter/self message

    Send an IC message to a character in your room. A whisper of the format
    "mutter player=Hello" will send a message in the form of "You mutter to
    <player>". A mutter of the format "mutter player=:does an emote" will appear
    in the form of "Discreetly, soandso does an emote" to <player>. 
    Some of what you mutter will be overheard by the room, but not all of it.
    It's possible to mutter to a list of targets.
    
    Characters with the enhanced senses ability can hear all of a mutter.

    The switch mutter/self does the partial pose to yourself, just for people
    overhearing the partial mutter.

    """

    key = "mutter"
    aliases = ["+mutter"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Social"
    simplified_key = "mutter"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        # get the messages we've sent (not to channels)
        if not caller.ndb.whispers_sent:
            caller.ndb.whispers_sent = []
        pages_we_sent = caller.ndb.whispers_sent
        # get last messages we've got
        if not caller.ndb.whispers_received:
            caller.ndb.whispers_received = []

        if not self.args:
            self.msg("Usage: mutter [<player> = msg]")
            return

        if "self" in self.switches:
        # todo, mutter/self
            return


        # We are sending. Build a list of targets
        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if not self.rhs:
            # MMO-type whisper. 'whisper <name> <target>'
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg(
                    "The MMO-style whisper format requires both a name and a message."
                )
                caller.msg(
                    "To send a message to your last whispered character, use {wwhisper =<message>"
                )
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))

        if not lhs and rhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Who do you want to whisper?")
                return
        else:
            receivers = lhslist

        recobjs = []
        for receiver in set(receivers):

            if isinstance(receiver, string_types):
                pobj = caller.search(receiver, use_nicks=True)
            elif hasattr(receiver, "character"):
                pobj = receiver.character
            elif hasattr(receiver, "player"):
                pobj = receiver
            else:
                self.msg("Who do you want to mutter to?")
                return
            if pobj:
                if hasattr(pobj, "has_account") and not pobj.has_account:
                    self.msg("You may only mutter to online characters.")
                elif not pobj.location or pobj.location != caller.location:
                    self.msg("You may only mutter to characters in the same room as you.")
                else:
                    recobjs.append(pobj)
        if not recobjs:
            self.msg("No one found to whisper.")
            return
        header = "{c%s{n whispers," % caller.name
        message = rhs
        mutter_text = ""
        # if message begins with a :, we assume it is a 'whisper-pose'
        if message.startswith(":"):
            message = "%s {c%s{n %s" % (
                "Discreetly,",
                caller.name,
                message.strip(":").strip(),
            )
            is_a_whisper_pose = True
        elif message.startswith(";"):
            message = "%s {c%s{n%s" % (
                "Discreetly,",
                caller.name,
                message.lstrip(";").strip(),
            )
            is_a_whisper_pose = True
        else:
            is_a_whisper_pose = False
            message = '"' + message + '"'

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)

        caller.ndb.whispers_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        rstrings = []
        for pobj in recobjs:
            otherobs = [ob for ob in recobjs if ob != pobj]
            if not pobj.access(caller, "tell"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            if is_a_whisper_pose:
                omessage = message
                if otherobs:
                    omessage = "(Also sent to %s.) %s" % (
                        ", ".join(ob.name for ob in otherobs),
                        message,
                    )
                pobj.msg(omessage, from_obj=caller, options={"is_pose": True})
            else:
                if otherobs:
                    myheader = header + " to {cyou{n and %s," % ", ".join(
                        "{c%s{n" % ob.name for ob in otherobs
                    )
                else:
                    myheader = header
                pobj.msg(
                    "%s %s" % (myheader, message),
                    from_obj=caller,
                    options={"is_pose": True},
                )
            if not pobj.ndb.whispers_received:
                pobj.ndb.whispers_received = []
            pobj.ndb.whispers_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name)
                # afk = pobj.player_ob and pobj.player_ob.db.afk
                # if afk:
                #     pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                #     rstrings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if rstrings:
            self.msg("\n".join(rstrings))
        if received:
            if is_a_whisper_pose:
                self.msg("You posed to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You whispered to %s, %s" % (", ".join(received), message))
                
                
            #partial intercept mutter functionality
            from random import randint
            word_list = rhs.split()
            chosen = []
            num_real = 0
            for word in word_list:
                if randint(0, 2):
                    chosen.append(word)
                    num_real += 1
                else:
                    chosen.append("...")
            if num_real:
                mutter_text = " ".join(chosen)
            if mutter_text:
                emit_string = ' mutters, "%s{n"' % mutter_text
                exclude = [caller] + recobjs
                caller.location.msg_action(
                    self.caller,
                    emit_string,
                    options={"is_pose": True},
                    exclude=exclude,
                    )
                self.mark_command_used()
        caller.posecount += 1



class CmdTightbeam(MuxCommand):

    """
    Tightbeam - send private IC message

    Usage:
      tightbeam[/switches] [<player>,<player>,... = <message>]
      tightbeam =<message> - sends a tightbeam radio to last person you radioed
      tightbeam <name> <message>
      2way <name> <message>     


    Send an IC message to a character anywhere on the game using in-game radio.

    You cannot send a tightbeam to a player whose radio is turned off.

    "+2way player=Hello" will send a message in the form of "Tightbeam from <player>:". 
    A 2way of the format "2way player=:does an emote" will appear
    in the form of "Tightbeam from <player> does an emote" to <player>. 

    +2way and +tightbeam do the same thing. For radio messages to talk within a group
    or on open bands, see the help for the +radio commands.
    """

    key = "tightbeam"
    aliases = ["+2way, +tightbeam", "2way"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        # get the messages we've sent (not to channels)
        if not caller.ndb.whispers_sent:
            caller.ndb.whispers_sent = []
        pages_we_sent = caller.ndb.whispers_sent
        # get last messages we've got
        if not caller.ndb.whispers_received:
            caller.ndb.whispers_received = []

        if not self.args:
            self.msg("Usage: tightbeam [<player> = msg]")
            return

        # We are sending. Build a list of targets

        #TODO - 2way needs to make sure a player's radio is on.

        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if not self.rhs:
            # MMO-type whisper. 'whisper <name> <target>'
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg(
                    "Tightbeam requires both a target or list of targets and message."
                )
                caller.msg(
                    "To send a radio message to the last person you mesasged, use {w2way =<message>"
                )
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))

        if not lhs and rhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Who do you want to tightbeam?")
                return
        else:
            receivers = lhslist

        recobjs = []
        for receiver in set(receivers):

            if isinstance(receiver, string_types):
                pobj = caller.search(receiver, use_nicks=True)
            elif hasattr(receiver, "character"):
                pobj = receiver.character
            elif hasattr(receiver, "player"):
                pobj = receiver
            else:
                self.msg("Who do you want to tightbeam?")
                return
            if pobj:
                if hasattr(pobj, "has_account") and not pobj.has_account:
                    self.msg("That charcter is not online.")

                else:
                    recobjs.append(pobj)
        if not recobjs:
            self.msg("No one found to whisper.")
            return
        header = "{c%s{n whispers," % caller.name
        message = rhs
        mutter_text = ""
        # if message begins with a :, we assume it is a 'whisper-pose'
        if message.startswith(":"):
            message = "%s {c%s{n %s" % (
                "Tightbeam from",
                caller.name,
                message.strip(":").strip(),
            )
            is_a_whisper_pose = True
        elif message.startswith(";"):
            message = "%s {c%s{n%s" % (
                "Tightbeam from",
                caller.name,
                message.lstrip(";").strip(),
            )
            is_a_whisper_pose = True
        else:
            is_a_whisper_pose = False
            message = '"' + message + '"'

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)

        caller.ndb.whispers_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        rstrings = []
        for pobj in recobjs:
            otherobs = [ob for ob in recobjs if ob != pobj]
            if not pobj.access(caller, "tell"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            if is_a_whisper_pose:
                omessage = message
                if otherobs:
                    omessage = "(Also sent to %s.) %s" % (
                        ", ".join(ob.name for ob in otherobs),
                        message,
                    )
                pobj.msg(omessage, from_obj=caller, options={"is_pose": True})
            else:
                if otherobs:
                    myheader = header + " to {cyou{n and %s," % ", ".join(
                        "{c%s{n" % ob.name for ob in otherobs
                    )
                else:
                    myheader = header
                pobj.msg(
                    "%s %s" % (myheader, message),
                    from_obj=caller,
                    options={"is_pose": True},
                )
            if not pobj.ndb.whispers_received:
                pobj.ndb.whispers_received = []
            pobj.ndb.whispers_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name)
                # afk = pobj.player_ob and pobj.player_ob.db.afk
                # if afk:
                #     pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                #     rstrings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if rstrings:
            self.msg("\n".join(rstrings))
        if received:
            if is_a_whisper_pose:
                self.msg("You tightbeam to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You tightbeam to %s, %s" % (", ".join(received), message))


            #to do, leave this as partial intercept.
                if "mutter" in self.switches or "mutter" in self.cmdstring:
                    from random import randint

                    word_list = rhs.split()
                    chosen = []
                    num_real = 0
                    for word in word_list:
                        if randint(0, 2):
                            chosen.append(word)
                            num_real += 1
                        else:
                            chosen.append("...")
                    if num_real:
                        mutter_text = " ".join(chosen)
                if mutter_text:
                    emit_string = ' mutters, "%s{n"' % mutter_text
                    exclude = [caller] + recobjs
                    caller.location.msg_action(
                        self.caller,
                        emit_string,
                        options={"is_pose": True},
                        exclude=exclude,
                    )
                    self.mark_command_used()
        caller.posecount += 1

class CmdSaraband(MuxCommand):
    """
    Saraband - send private IC message

    Usage:
      saraband[/switches] [<player>,<player>,... = <message>]
      saraband =<message> - sends whisper to last person you whispered
      saraband <name> <message>

    Send an IC message to a character in your room. A whisper of the format
    "whisper player=Hello" will send a message in the form of "You whisper
    <player>". A whisper of the format "whisper player=:does an emote" will appear
    in the form of "Discreetly, soandso does an emote" to <player>. It's generally
    expected that for whispers during public roleplay scenes that the players
    involved should pose to the room with some small mention that they're
    communicating discreetly. For ooc messages, please use the 'page'/'tell'
    command instead. If the /mutter switch is used, some of your whisper will
    be overheard by the room. Mutter cannot be used for whisper-poses.

    """

    key = "saraband"
    aliases = ["+saraband"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Capabilities"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        # get the messages we've sent (not to channels)
        if not caller.ndb.whispers_sent:
            caller.ndb.whispers_sent = []
        pages_we_sent = caller.ndb.whispers_sent
        # get last messages we've got
        if not caller.ndb.whispers_received:
            caller.ndb.whispers_received = []

        if not self.args:
            self.msg("Usage: saraband [<player> = msg]")
            return

        # We are sending. Build a list of targets
        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if not self.rhs:
            # MMO-type whisper. 'whisper <name> <target>'
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg(
                    "Saraband requires both a name and a message."
                )
                caller.msg(
                    "To send a message to your last whispered character, use {saraband =<message>"
                )
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))

        if not lhs and rhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Who do you want to contact?")
                return
        else:
            receivers = lhslist

        recobjs = []
        for receiver in set(receivers):

            if isinstance(receiver, string_types):
                pobj = caller.search(receiver, use_nicks=True)
            elif hasattr(receiver, "character"):
                pobj = receiver.character
            elif hasattr(receiver, "player"):
                pobj = receiver
            else:
                self.msg("Who do you want to contact?")
                return
            if pobj:
                if hasattr(pobj, "has_account") and not pobj.has_account:
                    self.msg("You may only send whispers to online characters.")
                elif not pobj.location or pobj.location != caller.location:
                    self.msg("You may only whisper characters in the same room as you.")
                else:
                    recobjs.append(pobj)
        if not recobjs:
            self.msg("No one found to whisper.")
            return
        header = "{c%s{n whispers," % caller.name
        message = rhs
        mutter_text = ""
        # if message begins with a :, we assume it is a 'whisper-pose'
        if message.startswith(":"):
            message = "%s {c%s{n %s" % (
                "Discreetly,",
                caller.name,
                message.strip(":").strip(),
            )
            is_a_whisper_pose = True
        elif message.startswith(";"):
            message = "%s {c%s{n%s" % (
                "Discreetly,",
                caller.name,
                message.lstrip(";").strip(),
            )
            is_a_whisper_pose = True
        else:
            is_a_whisper_pose = False
            message = '"' + message + '"'

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)

        caller.ndb.whispers_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        rstrings = []
        for pobj in recobjs:
            otherobs = [ob for ob in recobjs if ob != pobj]
            if not pobj.access(caller, "tell"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            if is_a_whisper_pose:
                omessage = message
                if otherobs:
                    omessage = "(Also sent to %s.) %s" % (
                        ", ".join(ob.name for ob in otherobs),
                        message,
                    )
                pobj.msg(omessage, from_obj=caller, options={"is_pose": True})
            else:
                if otherobs:
                    myheader = header + " to {cyou{n and %s," % ", ".join(
                        "{c%s{n" % ob.name for ob in otherobs
                    )
                else:
                    myheader = header
                pobj.msg(
                    "%s %s" % (myheader, message),
                    from_obj=caller,
                    options={"is_pose": True},
                )
            if not pobj.ndb.whispers_received:
                pobj.ndb.whispers_received = []
            pobj.ndb.whispers_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name)
                # afk = pobj.player_ob and pobj.player_ob.db.afk
                # if afk:
                #     pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                #     rstrings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if rstrings:
            self.msg("\n".join(rstrings))
        if received:
            if is_a_whisper_pose:
                self.msg("You posed to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You whispered to %s, %s" % (", ".join(received), message))
                if "mutter" in self.switches or "mutter" in self.cmdstring:
                    from random import randint

                    word_list = rhs.split()
                    chosen = []
                    num_real = 0
                    for word in word_list:
                        if randint(0, 2):
                            chosen.append(word)
                            num_real += 1
                        else:
                            chosen.append("...")
                    if num_real:
                        mutter_text = " ".join(chosen)
                if mutter_text:
                    emit_string = ' mutters, "%s{n"' % mutter_text
                    exclude = [caller] + recobjs
                    caller.location.msg_action(
                        self.caller,
                        emit_string,
                        options={"is_pose": True},
                        exclude=exclude,
                    )
                    self.mark_command_used()
        caller.posecount += 1


class CmdTelepath(MuxCommand):

    """
    Telepathy - send private IC message

    Usage:
      telepath [<player>,<player>,... = <message>]
      telepath =<message> - sends telepathy to last person you messaged
      telepath <name> <message>
      telepath/open

    Send a private IC message to a character on the game using 
    telepathy.
    
    A telepathic message of the format
    "telepath player=Hello" will send a message in the form of
    "A telepathic
    message from soandso: Hello." A telepathic message of the format 
    "telepath player=:does an emote" will appear
    in the form of "Telepathically, <emote>" to <player>. 
    Telepathy accepts multiple targets.
    
    Only one player with the telepath ability is necessary
    for a telepathic conversation. 
    
    The +telepath command may 
    be used among players in the same room as long as one or more
    of the involved players has the telepath skill.
    Other players in the same room as an active telepath, who also
    have the telepathy ability, may be able to detect telepathic
    messages sent privately, so be forewarned that this is not
    a perfectly private method of communication when other
    telepathic characters are present.

    To message a player with telepathy over a longer distance, use 
    +telepath/open to open a telepathic conduit. This allows 
    temporary use of two-way telepathy for two players.

    Todo/design: telepathic contact can be blocked with an IC skill.


    """

    key = "telepath"
    aliases = ["+telepath"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Capabilities"

    '''
    Some characters may in the future have the ability to block
    telepathic messages (not doing yet). 

    '''

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        # get the messages we've sent (not to channels)
        if not caller.ndb.whispers_sent:
            caller.ndb.whispers_sent = []
        pages_we_sent = caller.ndb.whispers_sent
        # get last messages we've got
        if not caller.ndb.whispers_received:
            caller.ndb.whispers_received = []

        if not self.args:
            self.msg("Usage: telepath [<player> = msg]")
            return

        # We are sending. Build a list of targets
        lhs = self.lhs
        rhs = self.rhs
        lhslist = self.lhslist
        if not self.rhs:
            # MMO-type whisper. 'whisper <name> <target>'
            arglist = self.args.lstrip().split(" ", 1)
            if len(arglist) < 2:
                caller.msg(
                    "Telepathy requires a target and a message."
                )
                caller.msg(
                    "To send a message to the last person you contacted, use {wtelepath =<message>"
                )
                return
            lhs = arglist[0]
            rhs = arglist[1]
            lhslist = set(arglist[0].split(","))

        if not lhs and rhs:
            # If there are no targets, then set the targets
            # to the last person we paged.
            if pages_we_sent:
                receivers = pages_we_sent[-1].receivers
            else:
                self.msg("Telepathically message who?")
                return
        else:
            receivers = lhslist

        recobjs = []
        for receiver in set(receivers):

            if isinstance(receiver, string_types):
                pobj = caller.search(receiver, use_nicks=True)
            elif hasattr(receiver, "character"):
                pobj = receiver.character
            elif hasattr(receiver, "player"):
                pobj = receiver
            else:
                self.msg("Who do you want to message?")
                return
            if pobj:
                if hasattr(pobj, "has_account") and not pobj.has_account:
                    self.msg("You may only send a message to online characters.")
                else:
                    recobjs.append(pobj)
        if not recobjs:
            self.msg("Can't find that player.")
            return
        header = "A telepathic message from {c%s," % caller.name
        message = rhs
        mutter_text = ""
        # if message begins with a :, we assume it is a 'whisper-pose'
        if message.startswith(":"):
            message = "%s {c%s{n %s" % (
                "Telepathically,",
                caller.name,
                message.strip(":").strip(),
            )
            is_a_whisper_pose = True
        elif message.startswith(";"):
            message = "%s {c%s{n%s" % (
                "Telepathically,",
                caller.name,
                message.lstrip(";").strip(),
            )
            is_a_whisper_pose = True
        else:
            is_a_whisper_pose = False
            message = '"' + message + '"'

        # create the temporary message object
        temp_message = TempMsg(senders=caller, receivers=recobjs, message=message)

        caller.ndb.whispers_sent.append(temp_message)

        # tell the players they got a message.
        received = []
        rstrings = []
        for pobj in recobjs:
            otherobs = [ob for ob in recobjs if ob != pobj]
            if not pobj.access(caller, "tell"):
                rstrings.append("You are not allowed to page %s." % pobj)
                continue
            if is_a_whisper_pose:
                omessage = message
                if otherobs:
                    omessage = "(Also sent to %s.) %s" % (
                        ", ".join(ob.name for ob in otherobs),
                        message,
                    )
                pobj.msg(omessage, from_obj=caller, options={"is_pose": True})
            else:
                if otherobs:
                    myheader = header + " to {cyou{n and %s," % ", ".join(
                        "{c%s{n" % ob.name for ob in otherobs
                    )
                else:
                    myheader = header
                pobj.msg(
                    "%s %s" % (myheader, message),
                    from_obj=caller,
                    options={"is_pose": True},
                )
            if not pobj.ndb.whispers_received:
                pobj.ndb.whispers_received = []
            pobj.ndb.whispers_received.append(temp_message)
            if hasattr(pobj, "has_account") and not pobj.has_account:
                received.append("{C%s{n" % pobj.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list their pages later."
                    % received[-1]
                )
            else:
                received.append("{c%s{n" % pobj.name)
                # afk = pobj.player_ob and pobj.player_ob.db.afk
                # if afk:
                #     pobj.msg("{wYou inform {c%s{w that you are AFK:{n %s" % (caller, afk))
                #     rstrings.append("{c%s{n is AFK: %s" % (pobj.name, afk))
        if rstrings:
            self.msg("\n".join(rstrings))
        if received:
            if is_a_whisper_pose:
                self.msg("You telepathically posed to %s: %s" % (", ".join(received), message))
            else:
                self.msg("You telepathically said to %s, %s" % (", ".join(received), message))
                
                #mutter self-switches, to-do, revise for partial intercepts

                if "mutter" in self.switches or "mutter" in self.cmdstring:
                    from random import randint

                    word_list = rhs.split()
                    chosen = []
                    num_real = 0
                    for word in word_list:
                        if randint(0, 2):
                            chosen.append(word)
                            num_real += 1
                        else:
                            chosen.append("...")
                    if num_real:
                        mutter_text = " ".join(chosen)
                if mutter_text:
                    emit_string = ' mutters, "%s{n"' % mutter_text
                    exclude = [caller] + recobjs
                    caller.location.msg_action(
                        self.caller,
                        emit_string,
                        options={"is_pose": True},
                        exclude=exclude,
                    )
                    self.mark_command_used()
        caller.posecount += 1


class CmdRadio(MuxCommand):

    """
    Stubbing out radio commands

    Usage:
      Radio
    """

    key = "radio"
    aliases = ["+radio"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        return
    

class CmdFrequency(MuxCommand):

    """
    Stubbing out radio commands

    Factional leaders and second in commands can set factional radio frequencies.

    Usage:
      freq
    """

    key = "freq"
    aliases = ["+freq"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        return