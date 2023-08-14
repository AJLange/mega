"""
Skills

Commands to make building stuff easier on staff. 
These commands are locked to staff and builders only.


"""

from evennia.server.sessionhandler import SESSIONS
import time
import re
from evennia import ObjectDB
from evennia import default_cmds, create_object
from evennia.utils import utils, create, evtable, make_iter, inherits_from, datetime_format
from server.utils import sub_old_ansi
from typeclasses.rooms import Room
from evennia import Command, CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from django.conf import settings
from typeclasses.cities import City
from typeclasses.cities import PersonalRoom, get_portal_tags
from typeclasses.rooms import PrivateRoom
from world.pcgroups.models import PlayerGroup



'''
Built attributes created by admin should be tamper-locked:
see here to add this later:
https://www.evennia.com/docs/0.9.5/Attributes.html#locking-and-checking-attributes
'''


class CmdMakeCity(MuxCommand):
    """
    
    +makecity
    A command to create a new city or factional base object.

    Usage:
      makecity <name>=<room>

    To create a new city (or base, etc) just use +makecity and the name of 
    what you want to create. 

    The required attribute <room> is the entry point to the city, where 
    players who enter the city object will end up when entering the city.

    In future iterations, we may lock certain cities to existing groups.

    """

    key = "makecity"
    aliases = "+makecity"
    help_category = "Building"
    locks = "perm(Builder))"

    def func(self):
        """Implements command"""
        caller = self.caller
        '''
        do I have build permissions?
        '''
        if not caller.check_permstring("builders"):
            caller.msg("Only staff can use this command. For players, see help construct.")
            return

        if not self.args:
            caller.msg("Usage: +makecity <Name>=<Landing Room>")
            return

        if "=" in self.args:
            cityname, enterroom = self.args.rsplit("=", 1)
            enterroom_valid = caller.search(enterroom, global_search=True)

            #should validate if this is a room

            if not inherits_from(enterroom_valid, settings.BASE_ROOM_TYPECLASS):
                caller.msg("Not a valid room.")
                return

            city = create_object("cities.City",key=cityname,location=caller.location,locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)
            '''
            link entry room to city created
            '''
            try:
                
                city.db.entry = enterroom
            except:
                caller.msg("Can't find a room called %s." % enterroom)
            caller.msg("Created the city: %s" % cityname)

        else: 
            caller.msg("Usage: +makecity <Name>=<Landing Room>")
            return

'''
Todo - return of the fix rooms command that makes rooms created into IC rooms 

'''

class CmdLinkTeleport(MuxCommand):
    """

    Usage:
       portalgrid <category>

    This command adds a room to the teleportation grid, making it a
    location that can be accessed with the +portal command 
    (see help +portal).

    This adds the room to the grid for good, until it is removed.  
    It will add it under the category that you specify.

    To add a room to the grid temporarily, use +plotroom.

    Current portal grid categories: Asia, Africa, Europe, North America, 
    Oceania, South America, Mars, Solar System, Locales, Faction, Other

    """

    key = "portalgrid"
    aliases = "+portalgrid"
    locks = "perm(Builder))"
    help_category = "Building"

    def func(self):
        """Implements command"""

        caller = self.caller
        room = caller.location

        '''
        do I have build permissions?
        '''
        if not caller.check_permstring("builders"):
            caller.msg("Only staff can use this command.")
            return

        if not self.args:
            caller.msg("You need to provide a portal category. See help +portalgrid.")
            return
        else:
            portal_tags = get_portal_tags()
            hub = self.args
            if hub in portal_tags:
                
                room.tags.add(hub, category ="portal")

                caller.msg("Added room %s to teleport category %s." % (room, hub) )
                return
            else:
                caller.msg("Not a valid portal category. See help portalgrid.")
        


class CmdPlotroom(MuxCommand):
    """
    
    Usage:
       plotroom

    This command temporarily adds a room to the grid for +portal. 

    It makes an announcement to the game so that everyone is aware of the 
    plot room.

    If a game is already on the grid as a plotroom, using +plotroom again 
    will remove it from the grid. 

    This setting is temporary and will clear out whenever the game is reset.

    """

    key = "plotroom"
    aliases = "+plotroom"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Player))"

    def func(self):
        """Implements command"""
        caller = self.caller
        room = caller.location
        if not room.teleport:
            room.teleport = True
            
        #doesn't work yet.


class CmdMakePrivateRoom(MuxCommand):
    """
    
    To dig out a private room object.

    Usage:
       construct <name of room>

    This creates an object, and a room inside that object.
    The room object is owned by you and can be picked up and moved
    around only by the original creator.

    """

    key = "construct"
    aliases = "+construct"
    help_category = "Building"
    locks = "cmd:all()"
    locks = "perm(Player))"

    new_room_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
    )

    def func(self):
        """Implements command"""
        caller = self.caller
        '''
        do I have build permissions? if so, remove build quota.
        '''
        if not caller.check_permstring("builders"):
            caller.db.roomquota = caller.db.roomquota -1

        if caller.db.roomquota < 1:
            caller.msg("Sorry, you are out of private room quota. +demolish an existing room to proceed.")
            return

        if not self.args:
            caller.msg("Usage: construct <Name of room>")
            return

            #should validate if this is a room
        roomname = self.args
        
        p_room = create_object("cities.PersonalRoom",key=roomname,location=caller.location,locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)
        '''
        link entry room to city created
        '''
        # Create the new room

        new_room = create.create_object(PrivateRoom, roomname, report_to=caller)
        lockstring = self.new_room_lockstring.format(id=caller.id)
        new_room.locks.add(lockstring)
        new_room.db.protector = []
        new_room.db.protector.append(caller)
        new_room.db.owner = caller
        
        try:
            p_room.db.entry = new_room
        except:
            caller.msg("Can't connect the room %s." % new_room)
            return

        # create an exit from this room

        exit_obj = create.create_object(
                typeclass=settings.BASE_EXIT_TYPECLASS,
                key="Exit <X>",
                location=new_room,
                aliases="x",
                locks=lockstring,
                report_to=caller,
            )
        if exit_obj:
            # storing a destination is what makes it an exit!
            exit_obj.destination = caller.location
            
            string = "Created new Exit from %s to %s." % (
                    new_room.name,
                    caller.location.name,
                            )

        caller.msg("Created the Private Room: %s" % p_room)
        caller.msg(string)
        

        return


class CmdDescInterior(MuxCommand):
    """
    Desc one of my private rooms.

    Usage:
        idesc <desc>

    When using idesc, I'm descing the room I'm standing in, so no other
    arguments are required. If this room does not belong to you, you cannot
    redesc it.

    """

    key = "idesc"
    aliases = "+idesc"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Player))"
    
    def func(self):
        """Implements command"""
        caller = self.caller
        here = caller.location
        id = caller.id
        # this isn't a foolproof lock check, but works OK
        if not here.db.owner == caller:
            caller.msg("You don't have permission to edit this desc.")
            return
        else:
            if not self.args:
                caller.msg("Update the desc to what?")
                return
            else:
                description = sub_old_ansi(self.args)
                here.db.desc = ("\n" + description + "\n")
                caller.msg("You update the desc of: %s" % here)


class CmdLockRoom(MuxCommand):
    """
    Lock your private room.

    Usage:
        +lock 

    When you are standing in a room you own, you can use +lock to prevent 
    other people from entering the room. This is for if you need privacy 
    for whatever reason.

    +lock does not prevent players from leaving your private room. You 
    cannot +lock someone in. It prevents entrance only. +lock will not lock
    the room owner out of their own room. Just everyone else.

    +lock only works on private rooms you own.
    It does not extend to rooms that you protect. (See help +protector)

    """

    key = "lock"
    aliases = "+lock"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Player))"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        here = caller.location

        #check if I own this room
        if here.db.owner == caller:
            if here.db.locked == False:
                here.db.locked = True
                caller.msg("Locked this room.")
                # find the exit and make sure it doesn't work
            else:
                caller.msg("This room is already locked.")
        else:
            caller.msg("Can't lock someone else's room!")


class CmdUnLockRoom(MuxCommand):
    """
    Unlock your private room.

    Usage:
        +unlock 

    A private room object looks like an object from the outside
    but behaves like a room on the inside.
    """

    key = "unlock"
    aliases = "+unlock"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Player))"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        here = caller.location

        #check if I own this room
        if here.db.owner == caller:
            if here.db.locked == True:
                here.db.locked = False
                caller.msg("Unlocked this room.")
                # I can now move freely into this room.
            else:
                caller.msg("This room is already unlocked.")
        else:
            caller.msg("Can't lock someone else's room!")


class CmdMyRooms(MuxCommand):
    """
    
    To find all rooms owned and protected by me.

    Usage:
       myrooms

    This gives you a list of all rooms owned by you (private rooms)
    and all rooms protected by you.

    It does not list rooms protected by your group.

    See also
    help construct
    help demolish

    """

    key = "myrooms"
    aliases = "+myrooms"
    help_category = "Building"
    locks = "cmd:all()"
    locks = "perm(Player))"

    def func(self):
        """Implements command"""
        caller = self.caller
        '''
        todo - the rest of the command
        first, search database for private rooms owned by me
        then search for the locations of the objects that match that

        then search database for non private rooms protected by me
        then generate a string to show all.
        
        '''
        return


class CmdDestroyPrivateRoom(MuxCommand):
    """
    
    To dig out a private room object.

    Usage:
       demolish <name of room>

    This will destroy a private room object that is controlled by you.
    This command cannot be reversed. Be sure you've taken any descs 
    you want to save before destroying your object.

    """

    key = "demolish"
    aliases = "+demolish"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Player))"

    #todo - confirm, do you really want to do this?

    def func(self):
        caller = self.caller
        room = self.args
        delete = True

        if not room:
            caller.msg("Demolish what?")
            delete = False
            return

        valid_room = ObjectDB.objects.object_search(room, typeclass=PrivateRoom)
        room_object = ObjectDB.objects.object_search(room, typeclass=PersonalRoom)
        #test

        if not room_object:
            caller.msg("No such personal room was found.")
            return
        if not valid_room:
            caller.msg("No such personal room was found.")
            return

        if not caller.check_permstring("builders"): 
            if valid_room[0].db.owner != caller:
                caller.msg("You can't demolish someone else's room.")
                return

        if len(valid_room) > 1 or len(room_object) > 1:
            caller.msg("Multiple matches, only deleting one.")
        else:
            had_exits = hasattr(valid_room[0], "exits") and valid_room[0].exits
            had_objs = hasattr(valid_room[0], "contents") and any(
                    obj
                    for obj in valid_room[0].contents
                    if not (hasattr(obj, "exits") and obj not in valid_room[0].exits)
                )

            string = "\n%s was destroyed." % room_object[0]
            if had_exits:
                string += " Exits to and from %s were destroyed as well." % room_object[0]
            if had_objs:
                string += " Objects inside %s were moved to their homes." % room_object[0]
            
            try:
                valid_room[0].delete()
                room_object[0].delete()
                caller.msg(string)
            except:
                caller.msg("Can't delete those objects.")
                return
            '''
            room is gone, so restore build quota.
            '''
            if not caller.check_permstring("builders"):
                caller.db.roomquota = caller.db.roomquota +1


class CmdCheckQuota(MuxCommand):
    """
    See my quota of personal rooms and items

    Usage:
        +quota

    This returns your remaining quota for creation of personal 
    rooms, items, and stages.

    """

    key = "quota"
    aliases = "+quota"
    help_category = "Building"
    locks = "perm(Player))"

    def func(self):
        caller = self.caller
        if caller.check_permstring("builders"):
            caller.msg("Builders have unlimited quota.")
            return
        else:
            room, craft, stage = caller.get_quotas()
        
            text = ("Your quota: \nPrivate rooms: %s/10 \nPersonal Objects: %s/10 \nStages: %s/10" % (room, craft, stage)) 
            caller.msg(text)
            return

class CmdProtector(MuxCommand):
    """
    See who is protecting a location.

    Usage:
        +protector

    This returns a list of the characters or groups that are protecting a 
    location on the grid.

    If you intend to do violence or scheming in a particular location,
    you should alert the protectors of a location before proceeding.

    If this returns the value 'Staff' in its list, that location
    is off-limits for violent scenes without asking staff first.

    """

    key = "protector"
    aliases = "+protector"
    help_category = "Building"
    locks = "perm(Player))"

    def func(self):
        """Implements command"""
        caller = self.caller
        room = caller.location
        if not room.db.protector:
            caller.msg("This room has no protector.")
        else:
            answer_string = ("This room is protected by: ")
            for protector in room.db.protector:
                answer_string = (answer_string + str(protector) + " ")
            caller.msg(answer_string)


class CmdSetProtector(MuxCommand):
    """
    Set the protector of a room.
    Staff only command.

    Usage:
        +setprotector <name>

    This command sets the protector of a current area, or adds
    to the list if there are muiltiple protectors. 

    A protector can be a Group, or a Player, or both.

    See help +protector.    
    
    """

    key = "setprotector"
    aliases = "+setprotector"
    locks = "perm(Builder))"
    help_category = "Building"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args
        room = caller.location

        #am I staff? be sure.

        if not caller.check_permstring("builders"):
            caller.msg("Only staff can use this command. If you need to set a protector contact a staffer.")
            return

        if not args:
            caller.msg("Add what protector?")
            return

        if not inherits_from(room, settings.BASE_ROOM_TYPECLASS):
                caller.msg("Not a valid room.")
                return
    
        if not room.db.protector:
            room.db.protector = []

        #accept 'staff' as a value. Staff over-rides other protectors.
        if args == "staff" or args == "Staff":
            room.db.protector.append("Staff")
            caller.msg("Set this room to staff-protected.")
            return

        #is the assigned thing a valid group? if not a group, then player?

        protector_here = self.caller.search(args, global_search=True)
        if not protector_here:
            caller.msg("No player or group found by that name.")
            return
        if inherits_from(protector_here, settings.BASE_CHARACTER_TYPECLASS):
            #we have a character, so add that
            room.db.protector.append(args)
            caller.msg("Added %s to this location's Protectors." % args)
            return

        # to do - group search doesn't work yet, this does not work. Fix it later

        elif PlayerGroup.objects.filter(protector_here):
            #it's a group, add that
            room.db.protector.append(args)
            caller.msg("Added the group %s to this location's Protectors." % args)
            return
        else:
            caller.msg("No player or group found by that name.")

class CmdClearProtector(MuxCommand):
    """
    Remove protectors from a room.
    Staff only command.

    Usage:
        +rmprotector

    This clears all protectors from the room you are in.
    This is a full reset for now, so if you want to just remove one protector,
    re-add the protectors you want to keep.
    
    """

    key = "rmprotector"
    aliases = "+rmprotector"
    locks = "perm(Builder))"
    help_category = "Building"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        room = caller.location

        #am I staff? be sure.

        if not caller.check_permstring("builders"):
            caller.msg("Only staff can use this command. If you need to set a protector contact a staffer.")
            return
        else:
            room.db.protector.clear()
            caller.msg("Cleared all protectors from this location.")
            return