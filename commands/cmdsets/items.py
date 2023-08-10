from evennia.commands.default.muxcommand import MuxCommand
from evennia import default_cmds, create_object
from evennia.utils import utils, create
from server.utils import sub_old_ansi
from typeclasses.objects import MObject
from typeclasses.gear import Item
from typeclasses.cities import PersonalRoom
from evennia import ObjectDB


class CmdCraft(MuxCommand):
    """
    Create a small object.
    Players will have a limited quota of miscellaneous objects.
    These objects can hold a desc, but have no other 
    functionality. 

    Usage:
        craft <name of object>
        eg
        craft Soccer Ball

    To desc your craft, use the +craftdesc command.
    To delete a craft you no longer need, use +junk.

    """

    key = "craft"
    aliases = "+craft"
    locks = "perm(Player))"
    help_category = "Building"
    
    new_obj_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
        )
    
    def func(self):
        """Implements command"""
        caller = self.caller
        '''
        check if I'm an admin. If I'm not admin, check and see if I have quota.
        '''
        if not caller.check_permstring("builders"):
            caller.db.craftquota = caller.db.craftquota -1
        
        #subtract from my available quota and make an object with no special properties.

        if caller.db.craftquota < 1:
            caller.msg("Sorry, you are out of craft quota. +junk a craft to proceed.")
            return

        if not self.args:
            caller.msg("Usage: craft <Name of item>")
            return

        iname = self.args
        
        
        new_obj = create_object("gear.Item",key=iname,location=caller.location,locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)

        lockstring = self.new_obj_lockstring.format(id=caller.id)
        new_obj.locks.add(lockstring)
        new_obj.db.owner = caller
        
        try:
            caller.msg("You created the item %s." % str(new_obj))
        except:
            caller.msg("Can't create %s." % str(new_obj))
            return

class CmdDescCraft(MuxCommand):
    """
    Write the desc for a small object that you have created.

    Usage:
        craftdesc <name of object>=<desc>
        eg
        craftdesc Soccer Ball=A round ball for kicking!
        odesc My Room=Odesc also works for this!

    To make a craft, use +craft.
    To delete a craft, use +junk.

    This can also be used to desc the outside of private rooms.
    
    """

    key = "craftdesc"
    aliases = ["+craftdesc", "odesc","+odesc"]
    locks = "perm(Player))"
    help_category = "Building"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args
        # this isn't a foolproof lock check, but works OK
        if not self.args:
            caller.msg("What do you want to desc?")
            return
        obj_desc = args.split("=")
        if len(obj_desc) < 1:
            caller.msg("Syntax error: use craftdesc <obj>=<desc>")
            return
        else:
            description = sub_old_ansi(obj_desc[1])
            obj = ObjectDB.objects.object_search(obj_desc[0], typeclass=Item)
            if not obj:
                obj = ObjectDB.objects.object_search(obj_desc[0], typeclass=PersonalRoom)
                if not obj:
                    caller.msg("No object by that name was found.")
                return
            if not obj[0].db.owner == caller:
                caller.msg("That object is not yours.")
                return
            obj[0].db.desc = ("\n" + description + "\n")
            caller.msg("You update the desc of: %s" % str(obj[0]))


class CmdJunkCraft(MuxCommand):
    """
    Destroy a crafted personal item that you don't need anymore.

    Usage:
        junk <name of object>
        eg
        junk Soccer Ball

    Junking can only occur with an item in your possession or
    in the same room as you, to prevent accidental junking.

    Junking an item will free up your quota to create a new
    item.
    
    To make a craft, use +craft.
    
    """

    key = "junk"
    alias = "+junk"
    locks = "perm(Player))"
    help_category = "Building"
    
    #todo: 'are you sure'

    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args

        if not args:
            caller.msg("What do you want to junk?")
            return

        valid_item = ObjectDB.objects.object_search(args, typeclass=Item)

        if not valid_item:
            caller.msg("No such personal craft was found.")
            return

        if not caller.check_permstring("builders"): 
            if valid_item[0].db.owner != caller:
                caller.msg("You can't junk that.")
                return

        try:
            valid_item[0].delete()
            caller.msg("Deleted %s" % str(valid_item[0]))
        except:
            caller.msg("Can't delete those objects.")
            return
        '''
        object is gone, so restore build quota.
        '''
        if not caller.check_permstring("builders"):
            caller.db.craftquota = caller.db.craftquota +1


class CmdSetQuota(MuxCommand):
    """
    This staff command can alter a person's craft and build quota.

    Usage:
        setquota/<type> <person>=<number>
        eg
        setquota/craft Rock=12
        
    Setquota takes the switches
    /craft
    /room
    /stage

    For the different types of quotas, and may take others in the future.
    The number should be an integer.
    
    """

    key = "setquota"
    alias = "+setquota"
    locks = "cmd:all()"
    help_category = "Building"
    locks = "perm(Builder))"
    switch_options = ("craft","stage","room")
    

    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args
        switches = self.switches
        errmsg = "Syntax error. See help setquota."

        if not caller.check_permstring("builders"):
            caller.msg("Admin only command.")
            return

        if not switches:
            caller.msg(errmsg)
            return
        else:
            char, number = args.split("=")
            if not number:
                caller.msg("Set what number?")
                return
        char_string = char.strip()
        char = self.caller.search(char_string, global_search=True)
        toggle = 0
        if "craft" in switches:
            toggle = "craftquota"
        if "room" in switches:
            toggle == "roomquota"
        if "stage" in switches:
            toggle == "stagequota"

        if not toggle:
            caller.msg(errmsg)
            return
        
        try:
            quota = int(number)
            if toggle == "craftquota":
                char.db.craftquota = quota
            if toggle == "roomquota":
                char.db.roomquota = quota
            if toggle == "stagequota":
                char.db.stagequota = quota
            caller.msg("You set the %s of %s to %i." %(toggle,char_string,quota))
            return
        except:
            caller.msg("This an error message. Something went wrong. Try again.")
            return



'''
notes here on player quotas:
10 items
10 personal rooms
10 stages

per player character.
Pets can only be created by staff for now (may change later)

'''