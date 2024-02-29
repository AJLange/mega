"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

from evennia import DefaultScript
import random
# from evennia import DefaultRoom, TICKER_HANDLER
from evennia import GLOBAL_SCRIPTS
from evennia.utils import create
from evennia.server.models import ServerConfig
from evennia.server.sessionhandler import SESSION_HANDLER, SESSIONS
from datetime import datetime, timedelta
from typeclasses.bboard import BBoard
from typeclasses.characters import Character
from typeclasses.accounts import Account



def get_all_boards():

    return


class Script(DefaultScript):
    """
    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.

    """

    pass


class WeightedPicker(object):
    def __init__(self):
        self.choices = []

    def add_option(self, option, weight):
        """
        Adds a option to this weighted picker.
        :param option: The option to add to the picker, any valid Python object.
        :param weight: An integer value to use as the weight for this option.
        """
        try:
            weight = int(weight)
        except ValueError:
            raise ValueError("Weight must be an integer value.")

        self.choices.append((option, weight))

    def pick(self):
        """
        Picks an option from those given to this WeightedPicker.
        """

        pickerdict = {}
        current_value = 0

        if len(self.choices) == 0:
            return None

        if len(self.choices) == 1:
            return self.choices[0][0]

        for option in self.choices:
            pickerdict[current_value] = option[0]
            current_value += option[1]

        picker = random.randint(0, current_value)
        last_value = 0
        result = None
        sorted_keys = sorted(pickerdict.keys())

        found = False
        for key in sorted_keys:
            if key >= picker:
                result = pickerdict[last_value]
                found = True
                continue
            last_value = key

        if not found:
            result = pickerdict[sorted_keys[-1]]

        return result
    

    
ECHOES = ["This is a test of the Save System", 
        "Fight on, for Everlasting Peace!",
        "We laugh darkly but we do not crash.",
        "Ping! Pong!"
        ] # etc  


class SaveScript(Script):
    "This script is ticked at regular intervals"
       
    def at_script_creation(self):
        "called only when the object is first created"
        self.key = "save_messages"
        self.desc = "The script that does cheeky save messages."
        self.interval = 60 * 60 #every hour, for now
        self.persistent = True

    def at_repeat(self):
        "ticked at regular intervals"
        echo = random.choice(ECHOES)
        for sess in SESSION_HANDLER.get_sessions():
            account = sess.get_account()
            if account:
                sess.msg(f"|wSAVE:|n {echo}")


class WeeklyEvents(Script):

    def at_script_creation(self):
        "called only when the object is first created"
        self.interval = 3600 * 24 * 7 #hour times day times week
        self.persistent = True

    def at_repeat(self):
        char = Character.objects.all()
        self.reset_votes(char)
        self.archive_jobs(char)

    def reset_votes(char):
        #do the thing
        for c in char:
            c.db.cookiequota = 5
        return
    
    def archive_jobs(char):
        #for all active jobs
        #do the thing
        return


class DailyEvents(Script):

    def at_script_creation(self):
        "called only when the object is first created"
        self.interval = 3600 * 24 #hour times day
        self.start_delay = True

    def at_repeat(self):
        self.check_weapon_timeouts()
        self.check_copy_timeouts()
        self.clean_bboards()

    def clean_bboards():
        #do the thing
        return
    
    def check_weapon_timeouts():
        #for all players with weapon copy skills

        #check if there are weapons past their use-by date


        #in the future, this might also process ride armor timeouts
        return
    
    def check_copy_timeouts():
        #for all players with armor copy skills

        #check if there are armors past their use-by date

        return
