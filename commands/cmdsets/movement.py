"""
All the stuff related to moving around the grid, such as 
teleport (override), follow, summon, are here.

"""


from evennia.objects.models import ObjectDB
from evennia.commands.default.building import CmdTeleport

from evennia.utils.evmenu import get_input
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.rooms import Room, PrivateRoom
from typeclasses.cities import City, PersonalRoom, get_portal_tags
from evennia.utils.search import search_tag, search_object
from evennia.utils.utils import inherits_from

class CmdSummon(MuxCommand):
    """
    summon

    Usage:
        summon <person>

    Summons a person to your location. 
    A summon invite can be turned down by choosing the option to deny.

    """

    key = "summon"
    aliases = ["+summon"]
    locks = "perm(Player)"
    help_category = "Travel"


    def func(self):
        """ Functionality for this mechanism. """
        caller = self.caller        
        args = self.args
        if not args:
            caller.msg("Summon who?")
            return

        port_targ = self.caller.search(self.args)
        if not port_targ:
            caller.msg("Can't find that player.")
            return
        try:
            #get confirmation first
            port_targ.msg(f"{caller} is trying to teleport to your location. Is this OK? Type accept to agree, deny to deny summon.")
            agreedeny = yield("Accept or Deny?")
            get_input(port_targ, agreedeny)
            if agreedeny.startswith('d'):
                port_targ.msg("Teleport denied.")
                caller.msg("Teleport was denied.")
                return
            elif agreedeny.startswith('a'):
                destination = caller.search(args, global_search=True)
                if not destination:
                    caller.msg("Destination not found.")
                    return
                if destination:
                    if not isinstance(destination, Room):
                        caller.msg("Destination is not a room.")
                    return
            else:
                caller.move_to(destination)
                caller.msg("Teleported to %s." % destination)

                return
        except:
            caller.msg("Error.")



class CmdJoin(MuxCommand):
    """
    Join a person on the grid.

    Usage:
        join <person>

    Asks another player to summon you to their location. 
    The player has to confirm your +join, then you will be teleported
    directly to their location.

    """

    key = "join"
    aliases = ["+join"]
    locks = "perm(Player)"
    help_category = "Travel"

    def agreedeny(caller, result):
        if result.lower() in ("agree", "a", "deny", "d"):
            return result
        else:
            caller.msg("Please answer if you agree or deny the teleport. ")
            return True

    def func(self):
        """ Functionality for this mechanism. """
        caller = self.caller
        args = self.args
        if not args:
            caller.msg("Join who?")
            return

        port_targ = self.caller.search(self.args)
        if not port_targ:
            caller.msg("Can't find that player.")
            return
        try:
            #get confirmation first
            port_targ.msg(f"{caller} is trying to teleport to your location. Is this OK? Type accept to agree, deny to deny summon.")
            agreedeny = yield("Accept or Deny?")
            get_input(port_targ, agreedeny)
            if agreedeny.startswith('d'):
                port_targ.msg("Teleport denied.")
                caller.msg("Teleport was denied.")
                return
            elif agreedeny.startswith('a'):
                destination = caller.search(args, global_search=True)
                if not destination:
                    caller.msg("Destination not found.")
                    return
                if destination:
                    if not isinstance(destination, Room):
                        caller.msg("Destination is not a room.")
                    return
            else:
                caller.move_to(destination)
                caller.msg("Teleported to %s." % destination)

                return

        except:
            caller.msg("Error.")


class CmdFollow(MuxCommand):
    """
    follow

    Usage:
        follow

    Starts following the chosen object. Use follow without
    any arguments to stop following. While following a player,
    you can follow them through locked doors they can open.

    To stop someone from following you, use 'ditch'.
    """

    key = "follow"
    aliases = "+follow"
    locks = "perm(Player)"
    help_category = "Travel"

    def func(self):
        """Handles followin'"""
        caller = self.caller
        args = self.args
        f_targ = caller.ndb.following
        if not args and f_targ:
            caller.stop_follow()
            return
        if not args:
            caller.msg("You are not following anyone.")
            return
        f_targ = caller.search(args)
        if not f_targ:
            caller.msg("No one to follow.")
            return
        caller.follow(f_targ)


class CmdDitch(MuxCommand):
    """
    ditch

    Usage:
        ditch
        ditch <list of followers>

    Shakes off someone following you. Players can follow you through
    any locked door you have access to.
    """

    key = "ditch"
    aliases = "+ditch"
    locks = "perm(Player)"
    aliases = ["lose"]
    help_category = "Travel"

    def func(self):
        """Handles followin'"""
        caller = self.caller
        args = self.args
        followers = caller.ndb.followers
        if not followers:
            caller.msg("No one is following you.")
            return
        if args:
            matches = []
            for arg in self.lhslist:
                obj = ObjectDB.objects.object_search(
                    arg, exact=False, candidates=caller.ndb.followers
                )
                if obj:
                    matches.append(obj[0])
                else:
                    AT_SEARCH_RESULT(obj, caller, arg)
            for match in matches:
                match.stop_follow()
            return
        # no args, so make everyone stop following
        if followers:
            for follower in followers:
                follower.stop_follow()
        caller.ndb.followers = []
        return



'''
Arx stuff to examine in more detail later:
'''


class CmdKeyring(MuxCommand):
    """
    Checks keys
    Usage:
        +keyring
        +keyring/remove <chest or room>

    Checks your keys, or Removes a key.
    """

    key = "+keyring"
    locks = "perm(Player)"
    help_category = "General"

    def func(self):
        """Executes keyring command"""
        caller = self.caller

        if "remove" in self.switches:
            removed = caller.item_data.remove_key_by_name(self.args.lower())
            if removed:
                self.msg("Removed %s." % ", ".join(ob.key for ob in removed))
        key_list = caller.held_keys.all()
        caller.msg("Keys: %s" % ", ".join(str(ob) for ob in key_list))



class CmdTidyUp(MuxCommand):
    """
    Removes idle characters from the room

    Usage:
        tidy

    This removes any character who has been idle for at least 4 hours in your 
    current room, provided that the room is public or a room you own.
    """

    key = "tidy"
    aliases = ["+gohomeyouredrunk", "+tidy"]
    locks = "perm(Player)"
    help_category = "General"

    def func(self):
        """Executes tidy command"""
        caller = self.caller
        loc = caller.location
        if inherits_from(loc,PersonalRoom) and not caller.check_permstring("builders"):
            owners = loc.db.owners or []
            if caller not in owners:
                self.msg("This is a private room that is not yours.")
                return
        from typeclasses.characters import Character

        # can only boot Player Characters
        chars = Character.objects.filter(db_location=loc)
        found = []
        for char in chars:
            time = char.idle_time
            
            if time > 14400:                
                found.append(char)
        if not found:
            self.msg("No characters were found to be idle.")
        else:
            for char in found:
                mapping = {"secret": True}
                char.move_to(char.home, mapping=mapping)
            self.msg(
                "The following characters were sent home: %s"
                % ", ".join(ob.name for ob in found)
            )



'''
make warp link-clickable with this

• |lc to start the link, by defining the command to execute.
• |lt to continue with the text to show to the user (the link text).
• |le to end the link text and the link definition.
'''

'''
discontinuing use of the SCS MUSH version of portals

class CmdWarp(MuxCommand):
    """
    teleport to another location
    Usage:
      warp <target location>
    Examples:
      warp granse - zerhem kingdom
    """

    key = "warp"
    aliases = "+warp"
    locks = "perm(Player)"

    # This is a copy-paste of @tel (or teleport) with reduced functions. @tel is an admin
    # command that takes objects as args, allowing you to teleport objects to places.
    # Warp only allows you to teleport yourself. I chose to make a new command rather than
    # expand on @tel with different permission sets because the docstring/help file is
    # expansive for @tel, as it has many switches in its admin version.

    def func(self):
        """Performs the teleport"""

        caller = self.caller
        args = self.args

        destination = caller.search(args, global_search=True)
        if not destination:
            caller.msg("Destination not found.")
            return
        if destination:
            if not isinstance(destination, Room):
                caller.msg("Destination is not an IC room.")
                return
            else:
                caller.move_to(destination)
                caller.msg("Teleported to %s." % destination)
'''

class CmdPortal(MuxCommand):
    """
    teleport to another location

    Usage:
      portal <location>
      portal/list


    This allows a player to teleport to the locations available on the 
    teleportation grid.

    Not all locations are on the teleportation grid. Teleport locations
    tend to be teleport hubs, hangouts, or scenes where an active 
    event is taking place.
    
    Use +portal/list to get a list of valid locations to teleport to.

    """

    key = "portal"
    aliases = "+portal", "port", "+port"
    locks = "perm(Player)"

    
    def func(self):
        """Performs the teleport"""

        caller = self.caller
        args = self.args

        if "list" in self.switches:
            #this search below is an example of how to categories db results by tag.
            locations = search_tag(category="portal")
            plotrooms = search_tag(category="plotroom")
            #todo: list format in a pretty grid with categories.
            teleport_message = ("Teleport locations available: \n")

            portal_tags = get_portal_tags()
            for portal in portal_tags:
                teleport_message = teleport_message + portal + (": \n")
                tele_cat = search_tag(portal, category="portal")
                for site in tele_cat:
                    site_label = str(site).split("-",1)
                    site_string = ("|lcportal " + str(site) + "|lt" + str(site_label[0]).strip() + "|le ")
                    teleport_message = teleport_message + site_string
                teleport_message = teleport_message + ("\n")
            for site in plotrooms:
                site_label = str(site).split("-",1)
                site_string = ("|lcportal " + str(site) + "|lt" + str(site_label[0]).strip() + "|le ")
                teleport_message = teleport_message + site_string

            '''
            for site in locations:
                site_label = str(site).split("-",1)
                site_string = ("|lcportal " + str(site) + "|lt" + str(site_label[0]).strip() + "|le ")
                teleport_message = teleport_message + site_string
            #teleport_message = (f"Teleport locations available: {', '.join(str(ob) for ob in locations)}")
            '''
            self.caller.msg(teleport_message)
            return

        else:
            #todo: Accept partial matches.
            
            locations = search_tag(category="portal")
            plotrooms = search_tag(category="plotroom")
            if not args:
                caller.msg("Portal to where?")
                return
            destination = caller.search(args, global_search=True)
            if not destination:
                caller.msg("Destination not found.")
                return
            if destination:
                if not isinstance(destination, Room):
                    caller.msg("Destination is not an IC room.")
                    return
                else:
                    if destination not in locations and destination not in plotrooms:
                        caller.msg("That is not a teleport-ok location. See portal/list.")
                    else:
                        caller.move_to(destination)
                        caller.msg("Teleported to %s." % destination)



#home doesn't care about private rooms or combat occuring for now

class CmdHome(MuxCommand):
    """
    
    Usage:
      home

    Teleports you to your home location.
    """

    key = "home"
    locks = "perm(Player)"
    help_category = "Travel"

    def func(self):
        """Implement the command"""
        caller = self.caller
        home = caller.home
        
        if not home:
            caller.msg("You have no home!")
        elif home == caller.location:
            caller.msg("You are already home!")

        else:
            mapping = {"secret": True}
            caller.move_to(home, mapping=mapping)
            caller.msg("There's no place like home ...")



class CmdLinkhere(MuxCommand):
    """
    linkhere
    Usage:
      +linkhere
    Sets a room as your IC home.
    """

    #todo: some permissions about what can and can't be set as home, for privacy purposes.

    key = "linkhere"
    locks = "perm(Player)"
    help_category = "Travel"

    def func(self):
        """Implement the command"""
        caller = self.caller
        home = caller.home

        if home == caller.location:
            caller.msg("You are already home!")
                
        elif not home:
            caller.msg("You set your home in this location.")
            caller.location = caller.home


class CmdEnterCity(MuxCommand):
    """
    Entering a city or private room object.
    
    Usage:
      enter <place>
      enter Neo Tokyo

    """

    key = "enter"
    locks = "perm(Player)"

    def func(self):
        caller = self.caller
        if not self.args:
            self.caller.msg("Enter where?")
            return
        #is this object an enterable place?
        destination = caller.search(self.args)
        if isinstance(destination, City):
            
            entry = (destination.db.entry)
            #todo - please add an exception handler to fail gracefully
            entry = Room.objects.get(db_key__startswith=entry)
            caller.msg("You enter the city.")
            emit_string = "%s is entering %s." % (caller.name, destination)
            caller.location.msg_contents(emit_string, from_obj=caller)
            self.caller.move_to(entry)

        elif isinstance(destination, PersonalRoom):            
            #check to see if i own this room
            #check to see if this room is unlocked before trying to enter.
            entry = (destination.db.entry)
            entry = PrivateRoom.objects.get(db_key__startswith=entry)
            if not entry.db.owner == caller:
                if entry.db.locked:
                    caller.msg("That room is locked.")
                    return
            caller.msg("You enter.")
            emit_string = "%s is entering %s." % (caller.name, destination)
            caller.location.msg_contents(emit_string, from_obj=caller)
            self.caller.move_to(entry)
        else:
            caller.msg("That isn't an enterable location.")

class CmdLeaveCity(MuxCommand):
    """
    Leaving a city object.
 
    Usage:
      leave

    When inside a room that is also an object, such as a private room,
    leave using this.

    """

    key = "leave"
    locks = "perm(Player)"

    def func(self):
        city = self.obj
        parent = city.location
        self.caller.move_to(parent)
