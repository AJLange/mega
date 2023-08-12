"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

'''
All commented out code needs rebuilt django models

'''

from evennia import default_cmds

#from commands.cmdsets.chargen import CmdStartChargen
from commands.cmdsets.pose import CmdThink, CmdPose, CmdMegaSay, CmdEmit, CmdOOCSay, CmdAside
from commands.cmdsets.charinfo import CmdFinger, CmdSheet, CmdCookieCounter, CmdCookie, CmdOOCFinger, CmdEFinger
#from commands.cmdsets.scenes import CmdPot
from commands.cmdsets.mail import CmdMail, CmdMailCharacter
from commands.cmdsets.movement import CmdHome, CmdDitch, CmdSummon, CmdJoin, CmdFollow, CmdWarp, CmdPortal

from commands import command
from commands.default.account import CmdOOC, CmdOOCLook, CmdWho, CmdCharCreate, CmdCharDelete
#from commands.cmdsets.combat import CmdRoll, CmdGMRoll, CmdFlip, CmdRollSet, CmdRollSkill, CmdTaunt, CmdPersuade, CmdIntimidate
#from commands.cmdsets.roster import CmdShowGroups, CmdSetGroups
#from commands.cmdsets.building import CmdLinkTeleport, CmdMakeCity, CmdProtector, CmdSetProtector, CmdClearProtector, CmdCheckQuota, CmdMakePrivateRoom, CmdDestroyPrivateRoom
#from commands.cmdsets.building import CmdLockRoom, CmdUnLockRoom, CmdDescInterior
#from commands.cmdsets.items import CmdCraft, CmdDescCraft, CmdSetQuota, CmdJunkCraft
#from commands.cmdsets.jobs import CmdRequest, CmdCheckJobs


from commands.cmdsets.descer import CmdDesc, CmdMultiDesc
from commands.cmdsets.utility import CmdWho, CmdICTime, CmdWarning, CmdHighlight
from commands.cmdsets.movement import CmdEnterCity, CmdLeaveCity
from commands.default.unloggedin import CmdUnconnectedCreate
# from commands.default.comms import CmdGrapevine2Chan, CmdIRC2Chan, CmdIRCStatus, CmdRSS2Chan
# from commands.default.comms import CmdChannelCreate, CmdCdestroy, CmdCBoot
# from commands.cmdsets.bboards import CmdBBCreate, CmdBBRead, CmdBBPost

# from evennia.contrib.dice import CmdDice
# from evennia.contrib import multidescer


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #