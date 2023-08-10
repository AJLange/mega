"""
Evennia settings file.

The available options are found in the default settings file found
here:

d:\documents\github\evennia\evennia\settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

'''
# We're looking for the number of seconds representing
# the date in 2235, since the game is set in the future.
# When going live, change this to the current date in 2235.
'''
from datetime import datetime
import time
start = datetime(2235, 8, 12, 20, 53)
epoch_start = time.mktime(start.timetuple())

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "M3"
GAME_SLOGAN = "Welcome to MegaMan MUSH! Increasingly Capcom MUSH."

DEFAULT_HOME = "#6"
START_LOCATION = "#6"


######################################################################
# Guest Accounts Unlocked
######################################################################

GUEST_ENABLED = True
# Typeclass for guest account objects (linked to a character)
BASE_GUEST_TYPECLASS = "typeclasses.accounts.Guest"
# The permission given to guests
PERMISSION_GUEST_DEFAULT = "Guests"
# The default home location used for guests.
GUEST_HOME = "#6"
# The start position used for guest characters.
GUEST_START_LOCATION = "#6"
# The naming convention used for creating new guest
# accounts/characters. The size of this list also determines how many
# guests may be on the game at once. The default is a maximum of nine
# guests, named Guest1 through Guest9.
GUEST_LIST = ["Guest" + str(s + 1) for s in range(20)]
ADDITIONAL_ANSI_MAPPINGS = [
    (r"%r", "\r\n"),
]
COMMAND_DEFAULT_ARG_REGEX = r"^[ /]+.*$|$"

MAX_CHAR_LIMIT = 8000
TIME_ZONE = "America/New_York"
MULTISESSION_MODE = 3

# The time factor dictates if the game world runs faster (timefactor>1)
# or slower (timefactor<1) than the real world.
TIME_FACTOR = 1

# The starting point of your game time (the epoch), in seconds.
# In Python a value of 0 means Jan 1 1970 (use negatives for earlier
# start date). This will affect the returns from the utils.gametime
# module.
TIME_GAME_EPOCH = epoch_start
WEBSERVER_PORTS = [(80,4001)]

'''

Django models. Will repair connections when all DBs are up

INSTALLED_APPS +=  ["world.roster", 
                    "world.scenes",
                    "world.msgs",
                    "world.groups", 
                    "world.requests",
                    "world.combat",
                    "world.boards",
                    "world.armor"]

'''

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")


