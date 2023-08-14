"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
# mygame/typeclasses/characters.py

from evennia import DefaultCharacter
from evennia.utils import ansi
import inflect

_INFLECT = inflect.engine()

class Character(DefaultCharacter):
    """
    [...]
    """
    def at_object_creation(self):
        """
        Called only at initial creation. 
        
        Intended use is that stats and skills are set as a 
        list and come in as a list from the chargen machine.
        """


        '''
        time to unfortunately refactor this as a character
        has armor modes and armor modes contain the stats

        and armor modes in turn hold weapons which contain the elemental
        properties

        '''

        # stats and basic setup

        self.db.pow = self.db.dex  = self.db.ten = self.db.cun = self.db.edu = self.db.chr = self.db.aur = 1

        #skills can't be null in combat testing
        # setting to 1 for now, will decide later if 0 is OK

        self.db.discern = self.db.aim = self.db.athletics =  self.db.force = self.db.mechanics = self.db.medicine = self.db.computer = self.db.stealth = self.db.heist = self.db.convince =  self.db.presence = self.db.arcana = 1

        self.db.size = "Medium"
        self.db.speed = "Medium"
        self.db.strength = "Normal"
        self.db.type = "Human"
        self.db.cookiecount = 0
        self.db.stagequota = 6
        self.db.roomquota = 10
        self.db.craftquota = 10

        self.db.files = []

        # transposing combat variables as they may change in the future
        self.set_initial_combat()
        
        # self.db.armor = []

        # Default display setup

        self.db.rollset = 1
        self.db.roomformat = 1
        self.db.in_stage = False
        self.db.stage = ""

        self.db.desc = "You see a character. Desc yourself with +mdesc and a new desc."
        self.db.multidesc = [("Default", "You see a character.")]
        self.db.nospoof = False


    def get_stats(self):
        """
        Simple access method to return ability
        scores as a tuple. 
        """
        return self.db.pow, self.db.dex, self.db.ten, self.db.cun, self.db.edu, self.db.chr, self.db.aur

    def get_a_stat(self, stat):

        #get a single stat.
        #to-do - not case sensitive

        if stat == "pow" or stat == "power":
            return self.db.pow
        elif stat == "dex" or stat == "dexterity":
            return self.db.dex
        elif stat == "ten" or stat == "tenacity":
            return self.db.ten
        elif stat == "cun" or stat == "cunning":
            return self.db.cun
        elif stat == "edu" or stat == "education":
            return self.db.edu
        elif stat == "chr" or stat == "charisma":
            return self.db.chr
        elif stat == "aur" or stat == "aura":
            return self.db.aur

        else:
            self.msg("No valid stat found.")
            return 0


    def get_skills(self):
        """
        Simple access method to return skills
    
        """
        return self.db.discern, self.db.aim, self.db.athletics, self.db.force, self.db.mechanics, self.db.medicine, self.db.computer, self.db.stealth, self.db.heist, self.db.convince, self.db.presence, self.db.arcana

    def get_a_skill(self, skill):
        #access a single skill

        if skill == "aim":
            return self.db.aim
        elif skill == "discern":
            return self.db.discern
        elif skill == "athletics":
            return self.db.athletics
        elif skill == "force":
            return self.db.force
        elif skill == "mechanics":
            return self.db.mechanics
        elif skill == "medicine":
            return self.db.medicine
        elif skill == "computer":
            return self.db.computer
        elif skill == "stealth":
            return self.db.stealth
        elif skill == "heist":
            return self.db.heist
        elif skill == "convince":
            return self.db.convince
        elif skill == "presence":
            return self.db.presence
        elif skill == "arcana":
            return self.db.arcana
        else:
            self.msg("No valid skill found.")
            return 0

    def get_finger(self):
        """
        haha, finger
        """
        return self.db.gender, self.db.type, self.db.quote, self.db.profile, self.db.game, self.db.function, self.db.specialties

    def get_ocfinger(self):
        return self.db.alias, self.db.prefemail, self.db.discord, self.db.rptimes, self.db.voice, self.db.altchars, self.db.info

    def get_statobjs(self):
        return self.db.type, self.db.size, self.db.capabilities, self.db.speed, self.db.weakness, self.db.resistance, self.db.elements, self.db.strength

    def get_quotas(self):
        return self.db.roomquota, self.db.craftquota, self.db.stagequota
    
    def get_numbered_name(self, count, looker, **kwargs):
        """
        simply overloading this method to squash pluralization of character objects
        """
        key = kwargs.get("key", self.key)
        key = ansi.ANSIString(key)  
        plural = key
        singular = key
                
        return singular, plural
    
    def get_groups(self):
        
        return self.db.groups

    def set_initial_combat(self):
        self.db.aimdice = 0
        self.db.chargedice = 0
        self.db.bonusdice = 0
        self.db.hp = 60
        self.db.active_weapon = "None"
        self.db.defending = 0
        return
    


    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    pass



