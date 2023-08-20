
from typeclasses.objects import Object
from evennia import Command, CmdSet
from evennia.commands.default.building import CmdTeleport
from evennia.objects.models import ObjectDB
from typeclasses.objects import Object
from typeclasses.exits import Exit
from evennia import DefaultExit


def get_portal_tags():
    #storing a list of valid portal tags here
    valid_tags = ["Asia", "Europe", "Faction"]
    return valid_tags

class City(Object):
    '''
    A type of object that, when entered, contains a 
    grid of rooms.

    a city has a persistent attribute called entry-room
    which indicates where you go when you walk in.
    we set this to a default then change it when
    making the city.
    '''

    def at_object_creation(self):

        self.db.desc = "Default City Description."
        self.db.entry = "City Landing"
        self.locks.add("get:false()")
        self.db.get_err_msg = "You can't take that."


        
''' 
to do, add this with teleport
https://www.evennia.com/docs/latest/api/evennia.objects.objects.html

here's how to do a moving one:
https://www.evennia.com/docs/latest/Tutorial-Vehicles.html

'''




class FactionBase(City):
    '''
    A type of city that can be infiltrated.
    Infiltration commands are, however, TBD,
    so for right now, this works just like
    any other city location.

    '''
    
    def at_object_creation(self):
        self.db.desc = "Default Base Description."
        


class Warship(FactionBase):
    '''
    A type of object that, when entered, contains a 
    grid of rooms, but is also mobile from room to room.

    Basically, a warship is a type of mobile city.
    Warships contain all commands for faction bases as well since
    they will never not belong to someone.
    '''

    def at_object_creation(self):
        self.db.desc = "Default Mobile Base Desc."


class PersonalRoom(Object):
    '''
    A personal Room is an object created by a player.
    Entering a personal room teleports the player to
    a single room on the grid which is their dedicated
    personal quarters room. 
    Personal Rooms can be picked up, moved, and re-desced.

    '''

    def at_object_creation(self):
        self.db.desc = "This is a personal room."
        self.locks.add("get:false()")
        self.db.get_err_msg = "You can't take a room."


class Stage(Object):
    '''
    A Stage is an object that, when entered, still broadcasts to 
    the room that it's in, but appends its name to the front of
    the pose.

    '''
    def at_object_creation(self):
        self.db.occupants =[]
        self.db.desc = "This is a Stage. Select using the 'select' command to append your location to the room."

class Vehicle(Stage):
    '''
    A vehicle is a type of Stage.
    The difference between a vehicle and an ordinary Stage
    is that a vehicle can be moved around from the inside via
    a series of driving commands.

    Doesn't work now. May not get used. Leaving it here anyway.

    '''

    def at_object_creation(self):
        self.db.desc = "This is a Stage. Enter it to append your location to the room."


