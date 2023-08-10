"""
Skills

Commands related to skill rolling and non-combat related skills.


"""

from math import floor
from math import randint
#from typing import AwaitableGenerator
from evennia.server.sessionhandler import SESSIONS
import time
import re
from evennia import ObjectDB, AccountDB
from evennia import default_cmds
from evennia.utils import utils, create, evtable, make_iter, inherits_from, datetime_format
from evennia.comms.models import Msg
from world.scenes.models import Scene, LogEntry
from typeclasses.rooms import Room
from world.supplemental import *
from evennia.contrib.dice import CmdDice



