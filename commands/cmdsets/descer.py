"""
Custom multidescer - Evennia's default refactored slightly for M3 use patterns.

"""
import re
from evennia import default_cmds
from evennia.objects.models import ObjectDB
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi

class DescValidateError(ValueError):
    "Used for tracebacks from desc systems"
    pass


#permissions on desc are strange. 
#todo, allow PCs to desc themselves, but not rooms.

class CmdDesc(MuxCommand):
    """
    describe an object or the current room.

    Usage:
      desc [<obj> =] <description>

    Sets the "desc" attribute on an object. If an object is not given,
    describe the current room.
    """

    key = "desc"
    aliases = "describe", "@desc"
    locks = "cmd:perm(desc) or perm(Builder)"
    help_category = "Building"


    def func(self):
        """Define command"""

        caller = self.caller
        if not self.args:
            caller.msg("Usage: desc [<obj> =] <description>")
            return


        if "=" in self.args:
            # We have an =
            obj = caller.search(self.lhs)
            if not obj:
                return
            desc = self.rhs or ""
        else:
            obj = caller.location or self.msg("|rYou can't describe oblivion.|n")
            if not obj:
                return
            desc = self.args
            desc = sub_old_ansi(desc)
        if obj.access(self.caller, "control") or obj.access(self.caller, "edit"):
            obj.db.desc = sub_old_ansi(desc)
            caller.msg("The new description was set on %s." % obj.get_display_name(caller))
        else:
            caller.msg("You don't have permission to edit the description of %s. For yourself, try +multidesc." % obj.key)


class CmdMultiDesc(MuxCommand):
    """

    Descing yourself with the multidescer.

    Usage:
       +multidesc = <text of desc>
       +mdesc = <text of desc>
       +multidesc/store <name>
       +multidesc/set <name>
       +multidesc/view <name>
       +multidesc/del <name>
       +multidesc/list
       +multidesc/all 
    
    Use the multidescer to describe yourself. 

    +multidesc/list to list your current descs.

    +multidesc/store stores your current desc under the name you
    have provided.

    +multidesc/set will put on a desc you've already stored.
    +multidesc/view shows the desc before you wear it.
    +multidesc/del to delete the desc by that name.

    +multidesc/all will list all your descs, and all the 
    text of those descs. This is mostly useful if you are
    about to drop a character and want to make sure your 
    descs are preserved before the character is wiped clean.

    +mdesc is an alias for +multidesc and does the same thing.

    This is just for descing yourself. To desc objects and rooms you own,
    use +odesc.

    To match a desc in your list to an armor form, see +armor.

    """

    key = "multidesc"
    aliases = ["+multidesc", "mdesc", "+mdesc"]
    switch_options = ("list","store","set","view", "del", "add","delete", "all")
    help_category = "Building"
    locks = "perm(Player))"

    def func(self):
        """Define command"""

        caller = self.caller
        args = self.args

        if "list" in self.switches:
            #_update_store(caller)
            desc_list = caller.db.multidesc
            outtext = "Stored Descs: \n"
            key_list = [key[0] for key in desc_list]
            for key in key_list:
                outtext += ("|w" + str(key)+ "|n, ")
            caller.msg(outtext)
            return

        if "store" in self.switches or "add" in self.switches:
            #_update_store(caller)
            if not args:
                caller.msg("Usage: +multidesc/store <name>")
                return
            desc_list = caller.db.multidesc
            cur_desc = caller.db.desc
            desc_list.append((args, cur_desc))
            caller.msg("Successfully stored desc %s." % args)
            return

        if "set" in self.switches:
            
            if not args:
                caller.msg("Usage: +multidesc/set <name>")
                return

            if args:
                key = args.lower()
                desc_list = caller.db.multidesc
                if not desc_list:
                    caller.msg("No multidescs set. See +help +multidesc.")
                    return
                for mkey, desc in desc_list:
                    mkey = mkey.lower()
                    if key == mkey:
                        caller.db.desc = desc
                        caller.msg("|wDecsription %s was set." % (key))
                        return
                caller.msg("Description '%s' not found." % key)
            else:
                caller.msg("|wCurrent desc:|n\n%s" % caller.db.desc)
            return    


        if "view" in self.switches:
            if args:
                key = args.lower()
                desc_list = caller.db.multidesc
                if not desc_list:
                    caller.msg("No multidescs set. See +help +multidesc.")
                    return
                for mkey, desc in desc_list:
                    mkey = mkey.lower()
                    if key == mkey:
                        caller.msg("|wDecsription %s:|n\n%s" % (key, desc))
                        return
                caller.msg("Description '%s' not found." % key)
            else:
                caller.msg("|wCurrent desc:|n\n%s" % caller.db.desc)
            return

        if "all" in self.switches:
            caller.msg("All descs:")
            desc_list = caller.db.multidesc
            for mkey, desc in desc_list:
                caller.msg("|wDecsription %s:|n\n%s\n" % (mkey, desc))
            return

        if "del" in self.switches or "delete" in self.switches:
            if not args:
                caller.msg("Usage: +multidesc/delete <name>")
                return

            desc_list = caller.db.multidesc
            
            key_list = [key[0] for key in desc_list]
            i = 0
            for desc_name in key_list:
                ldesc = desc_name.lower()
                match = args.lower()
                if ldesc == match:
                    del caller.db.multidesc[i]
                    caller.msg("Deleted description named '%s'." % args)
                    return
                i+=1
            # if we get here, didn't find that desc
            caller.msg("No desc named %s was found." % args)
            return

        else:
            try:
                if not args:
                    caller.msg("No desc provided. Nothing changed.")
                    return
                else:
                    desc = args
                    desc = ("\n" + sub_old_ansi(desc) + "\n")
                    caller.db.desc = str(desc)
                    caller.msg("The description was set.")
            except:
                caller.msg("Error in adding description. Check +help +multidesc.")
