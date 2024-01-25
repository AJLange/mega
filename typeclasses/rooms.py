"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils import create
from evennia.utils import search
from evennia.utils import logger
from evennia.utils import ansi
from typeclasses.objects import MObject
from collections import defaultdict
from evennia.utils.utils import (
    class_from_module,
    variable_from_module,
    lazy_property,
    make_iter,
    is_iter,
    list_to_string,
    to_str,
)



'''
eventually make use of this for special roomtypes
https://www.evennia.com/docs/0.9.5/Zones.html

you do not need that many discreet roomtypes if categorized
this way.

'''


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    def at_object_creation(self):
        self.db.protector = []
        self.db.sequence_beats = 0

    def at_say(
        self,
        message,
        msg_self=None,
        msg_location=None,
        receivers=None,
        msg_receivers=None,
        **kwargs,
    ):
        return message

    def msg_action(self, from_obj, no_name_emit_string, exclude=None, options=None):
        
        emit_string = "%s%s" % (
            "%s {c(%s){n" % (from_obj.name, from_obj.key),
            no_name_emit_string,
        )
            
        emit_string = "%s%s" % (from_obj, no_name_emit_string)
        self.msg_contents(
            emit_string,
            exclude=exclude,
            from_obj=from_obj,
            options=options,
            mapping=None,
        )
    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
        looker (Object): Object doing the looking.
        **kwargs (dict): Arbitrary, optional arguments for users
        overriding the call (unused by default).
        """
        if not looker:
            return ""
        # get and identify all objects
        visible = (con for con in self.contents if con != looker and con.access(looker, "view"))
        exits, users, destinations, things = [], [], [], defaultdict(list)
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
                destinations.append(con.destination)
            elif con.has_account:
                users.append("|c%s|n" % key)
            else:
            # things can be pluralized
                things[key].append(con)
        # get description, build string
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc

        '''
        todo: treat characters and objects and cities all differently here
        '''
        if users or things:
            # handle pluralization of things (never pluralize users)
            thing_strings = []
            for key, itemlist in sorted(things.items()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][0]
                thing_strings.append(key)
            string += "\n|wYou see:|n " + list_to_string(users + thing_strings)
        if exits:
            destination = 0
            string += "\n"
            for exit in exits:
                string += "\n " + list_to_string(exit) + " leads to " + list_to_string(destinations[destination])
                destination += 1
            string += "\n"

        return string


class OOCRoom(Room):
    """
    This is an OOC room that is missing play features but allows
    for people to go IC.
    
    Probably deprecated and won't be used. Saving just in case 
    we need to stash commands here.
    """
    def at_object_creation(self):
        "this is called only at first creation"


class StaffRoom(Room):
    """
    This room class is used by staff for lounges and such.
    """
    def at_object_creation(self):
        "this is called only at first creation"      

class ChargenRoom(StaffRoom):
    """
    This room class is used by character-generation rooms. It makes
    the ChargenCmdset available.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        


class TrainingRoom(Room):
    """
    This is an IC room that allows for no holds barred combat
    """
    def at_object_creation(self):
        "this is called only at first creation"



class QuartersRoom(Room):
    """
    This room type would allow people to set down quarters rooms of their own.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        
        
class Cockpit(Room):
    """
    This room type is for driving mobile bases
    """
    def at_object_creation(self):
        "this is called only at first creation"



class PrivateRoom(Room):
    """
    A type of IC room with some additional lock functions.
    """
    def at_object_creation(self):
        # private rooms have an owner, the owner is also the protector.
        # try getting the contents since the first person in should be owner.
        # this wont work long term prevents breaking for now.
        self.db.locked = False


class PlayRoom(Room):
    """
    Deprecated - wasn't needed, saved for DB reasons
    """
    def at_object_creation(self):
        "this is called only at first creation"


class WaterRoom(Room):
    """
    This room type is for rooms that are also underwater
    """
    def at_object_creation(self):
        "this is called only at first creation"

class SpaceRoom(Room):
    """
    This room type is for rooms that are in space or Zero-G
    """
    def at_object_creation(self):
        "this is called only at first creation"

class NexusRoom(Room):
    """
    This room type is for rooms that have strong magical resonance
    """
    def at_object_creation(self):
        "this is called only at first creation"

class BurrowRoom(Room):
    """
    This room type is for rooms that are under open ground
    """
    def at_object_creation(self):
        "this is called only at first creation"


class NetRoom(Room):
    """
    This room type is for rooms that are on the internet.
    """
    def at_object_creation(self):
        "this is called only at first creation"


class MovieRoom(OOCRoom):
    """
    This room type is for OOC style rooms that would allow watching scenes
    without participating in them. For guests.
    """
    def at_object_creation(self):
        "this is called only at first creation"