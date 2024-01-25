import random
from evennia import DefaultRoom, TICKER_HANDLER
from typeclasses.scripts.scripts import Script
from evennia.utils import create
from typeclasses.scripts import gametime
from evennia.server.models import ServerConfig
from evennia.server.sessionhandler import SESSION_HANDLER
from datetime import datetime, timedelta
from typeclasses.bboard import BBoard
from typeclasses.accounts import Account

    
ECHOES = ["This is a test of the Save System", 
        "Fight on, for Everlasting Peace!",
        "Maybe it's not necessary to write save here, why do we even do that?",
        "These emits do not have a character limit anymore, but they probably should be kept brief regardless"
        ] # etc  


class SaveScript(Script):
    "This script is ticked at regular intervals"        
       
    def at_script_creation(self):
        "called only when the object is first created"
        TICKER_HANDLER.add(60 * 60, self.announce_save)

    def announce_save(self, *args, **kwargs):
        "ticked at regular intervals"
        echo = random.choice(ECHOES)
        for sess in SESSION_HANDLER.get_sessions():
            account = sess.get_account()
            if account:
                sess.msg(f"|wSAVE:|n {echo}")


class WeeklyEvents(Script):

    def at_script_creation(self):
        "called only when the object is first created"
        self.interval = 3600
        self.start_delay = True
        self.attributes.add("run_date", datetime.now() + timedelta(days=7))

    def at_start(self, **kwargs):
        super(WeeklyEvents, self).at_start(**kwargs)

    def do_weekly_events(self, reset=True):
        # schedule next weekly update for one week from now
        self.db.run_date += timedelta(days=7)
        self.reset_votes()
        self.archive_jobs()

    def reset_votes():
        #do the thing
        return
    
    def archive_jobs():
        #for all active jobs

        return


class DailyEvents(Script):

    def at_script_creation(self):
        "called only when the object is first created"
        self.interval = 3600
        self.start_delay = True
        self.attributes.add("run_date", datetime.now() + timedelta(days=7))

    def at_start(self, **kwargs):
        super(WeeklyEvents, self).at_start(**kwargs)

    def do_weekly_events(self, reset=True):
        # schedule next weekly update for one week from now
        self.db.run_date += timedelta(days=1)
        self.check_weapon_timeouts()
        self.clean_bboards()

    def clean_bboards():
        #do the thing
        return
    
    def check_weapon_timeouts():
        #for all players with weapon copy skills

        #check if there are weapons past their use-by date
        #for all players with armor copy skills

        #check if there are armors past their use-by date


        #in the future, this might also process ride armor timeouts
        return
