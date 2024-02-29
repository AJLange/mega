"""
Commands related to getting information about characters.

Finger, OOCFinger, Efinger (aka IC finger)

To add: FClist related commands
Commands related to FC sorting

Other fun info options as needed
"""


from evennia import CmdSet
from evennia import ObjectDB
from commands.command import BaseCommand
from evennia.commands.default.muxcommand import MuxCommand
from server.utils import sub_old_ansi
from math import floor
from evennia.utils.search import object_search
from evennia.utils.utils import inherits_from
from django.conf import settings
from world.combat.models import Weapon
from server.battle import process_elements, process_attack_class, process_effects, get_element_text, get_class_text, get_effect_text, num_to_line, listcap_to_string, num_to_skill

class CmdFinger(BaseCommand):
    """
    Usage:
      finger <character>

    To get basic IC profile information about a character.

    Useful for an OOC overview and for potential appers. Information 
    here is a combination of what is known publically as well as what 
    is more general about a character's personality and backstory and 
    is more individual to the character.

    Players should not necessarily assume they ICly know everything about
    what is in another player's +finger. For information that is IC
    and public, use +efinger. (which is also aliased to +info)

    """
    key = "finger"
    aliases = ["+finger", "+figner", "figner", "profile", "+profile"]
    lock = "cmd:all()"
    help_category = "General"

    def func(self):
        "This performs the actual command"
        if not self.args:
            self.caller.msg("Finger who?")
            return

        # find a player in the db who matches this string
        # todo- match on alias 
        char_string = self.args.strip()
        char = self.caller.search(char_string, global_search=True)

        #should validate if this is a character
        
        if not char:
            self.caller.msg("Character not found.")
            return
        
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Character not found.")
            return

        try:
            name = char.name
            gender, type, quote, profile, game, function, specialties = char.get_finger()

            border = "------------------------------------------------------------------------------"
            line1 = "Name: %s"  % (name)               
            line2= "Template: %s  Function: %s"  % (type, function)
            line3 = "Gender: %s Game: %s"  % (gender, game)
            line4 = "%s" % (quote)
            line5 = "%s" % (profile)
            line6 = "%s" % (specialties)

            fingermsg = (border + "\n\n" + line1 + "\n\n" + line2 + "\n" + line3 + "\n\n" + line4  + "\n\n" + line5 + "\n\n" + line6 +  "\n\n" + border + "\n")
            self.caller.msg(fingermsg)
            return
        except ValueError:
            self.caller.msg("Not a valid character.")
            return
        


class CmdEFinger(MuxCommand):
    """
    Usage:
      efinger <character>
      info <character>

      efinger/<category> <info>
      Ex:
        efinger/email mega@mush.com

      efinger/born
      efinger/created
      efinger/both

    To get basic IC information about a character. Usually set to what is publically 
    known or can be looked up about a character from an IC standpoint, including their 
    reputation and known abilities.

    Players can fill these out themselves, but staff has a right to double-check this 
    information for accuracy. You may fill out as much or as little of your +efinger as 
    you like, depending on what can be ICly known or interesting to share. Use the 
    command with switches to do this, as above: efinger/email <myICemail> etc.

    The final command toggles if your character was 'born,' 'built,' or both. 
    Use this to change the born-on date line to a created-on date line,
    or, to add both fields if you feel those are necessary.
    
    """
    key = "efinger"
    aliases = ["+efinger", "+efigner", "efigner", "info", "+info"]
    lock = "cmd:all()"
    help_category = "General"

    def func(self):
        "This performs the actual command"

        caller = self.caller
        switch = self.switches

        # setting attributes switches

        
        if "email" in switch:
            if self.args:
                caller.db.prefemail = sub_old_ansi(self.args)
                self.msg("IC Email set to: %s" % self.args)
            else:
                caller.attributes.remove("prefemail")
                self.msg("Email address cleared.")
            return
        if "born" in switch:
            self.msg("Character given the Birthday field.")
            caller.db.was_born = True
            caller.db.was_created = False
            return
        if "created" in switch:
            self.msg("Character given the Created On field.")
            caller.db.was_created = True
            caller.db.was_born = False
            return
        if "both" in switch:
            self.msg("Character given the Birthday and Created On fields.")
            caller.db.was_born = True
            caller.db.was_created = True
            return
        if "adddate" in switch:
            if self.args:
                caller.db.rptimes = sub_old_ansi(self.args)
                self.msg("RP Times set to: %s" % self.args)
            else:
                caller.attributes.remove("rptimes")
                self.msg("RP Times cleared.")
            return
        if "cleardate" in switch:
            if self.args:
                caller.db.voice = sub_old_ansi(self.args)
                self.msg("Voice set to: %s" % self.args)
            else:
                caller.attributes.remove("voice")
                self.msg("Voice cleared.")
            return
        if "info" in self.switches or "Info" in self.switches:
            if self.args:
                caller.db.info = sub_old_ansi(self.args)
                self.msg("Info set to: %s" % self.args)
            else:
                caller.attributes.remove("info")
                self.msg("Info cleared.")
            return
            '''
            I want a better error message here but I'll fix this during formatting later.
            else:
            self.msg("Not a valid oocfinger attribute. See +help +oocfinger.")
            also, maybe put charlimits on the above.
            '''

        if not self.args:
            char = caller
        else:     
        # find a player in the db who matches this string
            char_string = self.args.strip()
            char = self.caller.search(char_string, global_search=True)
        if not char:
            caller.msg("Character not found.")
            return

        #is it a character? 
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Character not found.")
            return
        try:
            # build the string for efinger
            
            name = char.name
            alias, icemail, s_num, birthplace, notes = char.get_efinger()
            parents, birthday, creator, builddate = char.get_creators()
            gender = char.db.gender
            border = "------------------------------------------------------------------------------"
            line1 = "Name: %s Alias: %s"  % (name, alias)          
            line2= "Email: %s  Gender: %s"  % (icemail, gender)
            
            if char.db.was_created and not char.db.was_born:
                line3 = "Creator: %s Created On: %s" % (creator, builddate)
                line4 = "Serial Number: %s" % (s_num)
            elif char.db.was_born and char.db.was_created:
                line3 = "Parents: %s Birthday: %s \nCreator: %s Created On: %s" % (parents, birthday, creator, builddate)
                line4 = "Birthplace: %s Serial Number: %s" % (birthplace, s_num)
            elif char.db.was_born and not char.db.was_created:
                line3 = "Parents: %s Birthday: %s" % (parents, birthday)
                line4 = "Birthplace: %s" % (birthplace)
            elif not char.db.was_born and not char.db.was_created:
                #default if nothing set
                char.db.was_created = True
                line3 = "Creator: %s Created On: %s" % (creator, builddate)
                line4 = "Serial Number: %s" % (s_num)
            line5 = "Groups: "
            line6 = "Notes: %s" % (notes)

            fingermsg = (border + "\n\n" + line1 + "\n\n" + line2 + "\n" + line3 + "\n\n" + line4  +  "\n\n" + line5 + "\n\n" + line6 +  "\n\n" + border + "\n")
            
            caller.msg(fingermsg)
        except ValueError:
            caller.msg("Some error occured.")
            return


class CmdOOCFinger(MuxCommand):
    """
    
    Usage:
      +oocfinger <character>

      +oocfinger/discord <Your Discord here>
      +oocfinger/email <Your Email here>
    
    To get basic OOC information which relates to the player of the character. 
    You can find personal RP hooks and other preferences set here, as well 
    as any OOC contact information the player feels comfortable to provide.

    Set with switches such as +oocfinger/altchars to add the fields provided 
    to your own OOC finger.

    Fields included:

    Email, Alias, Discord, Altchars, RPTimes, Timezone, Voice, Info 

    "Info" is for free response where you can set RP preferences and hooks 
    or anything you like. Timezone should update automatically.
    
    """
    key = "oocfinger"
    aliases = ["+oocfinger","ofinger", "+ofigner", "ofigner", "+oocfigner"]
    lock = "cmd:all()"
    help_category = "General"

    def func(self):
        "This performs the actual command"
        caller = self.caller

    # setting attributes switches
    # first pass
        
        if "email" in self.switches or "Email" in self.switches:
            if self.args:
                caller.db.prefemail = sub_old_ansi(self.args)
                self.msg("Email set to: %s" % self.args)
            else:
                caller.attributes.remove("prefemail")
                self.msg("Email address cleared.")
            return
        if "discord" in self.switches or "Discord" in self.switches:
            if self.args:
                caller.db.discord = sub_old_ansi(self.args)
                self.msg("Discord set to: %s" % self.args)
            else:
                caller.attributes.remove("discord")
                self.msg("Discord cleared.")
            return
        if "altchars" in self.switches or "Altchars" in self.switches or "alts" in self.switches or "Alts" in self.switches in self.switches:
            if self.args:
                caller.db.altchars = sub_old_ansi(self.args)
                self.msg("AltChars set to: %s" % self.args)
            else:
                caller.attributes.remove("altchars")
                self.msg("Alts cleared.")
            return
        if "rptimes" in self.switches or "RPtimes" in self.switches or "Rptimes" in self.switches:
            if self.args:
                caller.db.rptimes = sub_old_ansi(self.args)
                self.msg("RP Times set to: %s" % self.args)
            else:
                caller.attributes.remove("rptimes")
                self.msg("RP Times cleared.")
            return
        if "voice" in self.switches or "Voice" in self.switches:
            if self.args:
                caller.db.voice = sub_old_ansi(self.args)
                self.msg("Voice set to: %s" % self.args)
            else:
                caller.attributes.remove("voice")
                self.msg("Voice cleared.")
            return
        if "info" in self.switches or "Info" in self.switches:
            if self.args:
                caller.db.info = sub_old_ansi(self.args)
                self.msg("Info set to: %s" % self.args)
            else:
                caller.attributes.remove("info")
                self.msg("Info cleared.")
            return
            '''
            I want a better error message here but I'll fix this during formatting later.
            else:
            self.msg("Not a valid oocfinger attribute. See +help +oocfinger.")
            also put charlimits on some of the items above.
            '''

        if not self.args:
            char = caller
        else:     
        # find a player in the db who matches this string
            char_string = self.args.strip()
            char = self.caller.search(char_string, global_search=True)
        if not char:
            caller.msg("Character not found.")
            return

        #is it a character? 
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Character not found.")
            return
        try:
            # build the string for ooc finger

            name = char.name
            alias, prefemail, discord, rptimes, voice, altchars, info = char.get_ocfinger()

            border = "------------------------------------------------------------------------------"
            line1 = "Name: %s Alias: %s"  % (name, alias)               
            line2= "Email: %s  Discord: %s"  % (prefemail, discord)
            line3 = "RP Times: %s Voice: %s"  % (rptimes, voice)
            line4 = "Alts: %s" % (altchars)
            line6 = "Info: %s" % (info)

            fingermsg = (border + "\n\n" + line1 + "\n\n" + line2 + "\n" + line3 + "\n\n" + line4  +  "\n\n" + line6 +  "\n\n" + border + "\n")
            
            caller.msg(fingermsg)
        except ValueError:
            caller.msg("Some error occured.")
            return
        

'''
Not high priority, but to be converted and added as a stretch feature

class CmdRPHooks(MuxCommand):
    """
    Sets or searches RP hook tags
    Usage:
        +rphooks <character>
        +rphooks/search <tag>
        +rphooks/add <searchable title>[=<optional description>]
        +rphooks/rm <searchable title>
    """

    key = "+rphooks"
    help_category = "Social"
    aliases = ["rphooks"]

    def list_valid_tags(self):
        """Lists the existing tags for rp hooks"""
        tags = Tag.objects.filter(db_category="rp hooks").order_by("db_key")
        self.msg("Categories: %s" % "; ".join(tag.db_key for tag in tags))
        return

    def func(self):
        """Executes the RPHooks command"""
        if not self.switches:
            if not self.args:
                targ = self.caller
            else:
                targ = self.caller.search(self.args)
                if not targ:
                    self.list_valid_tags()
                    return
            hooks = targ.tags.get(category="rp hooks") or []
            hooks = make_iter(hooks)
            hook_descs = targ.db.hook_descs or {}
            table = EvTable("Hook", "Desc", width=78, border="cells")
            for hook in hooks:
                table.add_row(hook, hook_descs.get(hook, ""))
            table.reformat_column(0, width=20)
            table.reformat_column(1, width=58)
            self.msg(table)
            if not hooks:
                self.list_valid_tags()
            return
        if "add" in self.switches:
            title = self.lhs.lower()
            if len(title) > 25:
                self.msg("Title must be under 25 characters.")
                return
            # test characters in title
            if not self.validate_name(title):
                return
            data = self.rhs
            hook_descs = self.caller.db.hook_descs or {}
            self.caller.tags.add(title, category="rp hooks")
            if data:
                hook_descs[title] = data
                self.caller.db.hook_descs = hook_descs
            data_str = (": %s" % data) if data else ""
            self.msg("Added rphook tag: %s%s." % (title, data_str))
            return
        if "search" in self.switches:
            table = EvTable("Name", "RPHook", "Details", width=78, border="cells")
            if not self.args:
                self.list_valid_tags()
                return
            tags = Tag.objects.filter(
                db_key__icontains=self.args, db_category="rp hooks"
            )
            for tag in tags:
                for pc in tag.accountdb_set.all():
                    hook_desc = pc.db.hook_descs or {}
                    desc = hook_desc.get(tag.db_key, "")
                    table.add_row(pc, tag.db_key, desc)
            table.reformat_column(0, width=10)
            table.reformat_column(1, width=20)
            table.reformat_column(2, width=48)
            self.msg(table)
            return
        if "rm" in self.switches or "remove" in self.switches:
            args = self.args.lower()
            hook_descs = self.caller.db.hook_descs or {}
            if args in hook_descs:
                del hook_descs[args]
                if not hook_descs:
                    self.caller.attributes.remove("hook_descs")
                else:
                    self.caller.db.hook_descs = hook_descs
            tagnames = self.caller.tags.get(category="rp hooks") or []
            if args not in tagnames:
                self.msg("No rphook by that category name.")
                return
            self.caller.tags.remove(args, category="rp hooks")
            self.msg("Removed.")
            return
        self.msg("Invalid switch.")

    def validate_name(self, name):
        """Ensures that RPHooks doesn't have a name with special characters that would break it"""
        import re

        if not re.findall("^[\w',]+$", name):
            self.msg("That category name contains invalid characters.")
            return False
        return True

'''

class CmdSoundtrack(BaseCommand):
    '''
    Soundtrack command not yet added.
    '''
    def func(self):
        "This performs the actual command"
        self.caller.msg("Not yet added.")
        return

class CmdSheet(BaseCommand):
        """
        List my stats

        Usage:
          stats

        Displays a list of your current stats.
        """
        key = "stats"
        aliases = ["+stats", "sheet", "+sheet"]
        locks = "perm(Player)"
        help_category = "General"

        def func(self):
            """implements the actual functionality"""
            caller = self.caller

            # if I'm staff, I can look at other character's sheets

            if self.args:
                if not caller.check_permstring("builders"):
                    caller.msg("Only staff can check other player's stats. stats to see your own stats.")
                    return
                else:
                    name = self.args.strip()
                    name = name.title()
                    char = caller.search(name, global_search=True) 
                    if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                        self.caller.msg("Character not found.")
                        return

            else:
                name = caller.name
                char = caller

            types, size, speed, strength = char.get_statobjs()
            pow, dex, ten, cun, edu, chr, aur = char.get_stats()
            cap = char.get_caps()
            cap = listcap_to_string(cap)
            armor = char.get_current_armor()
            all_armors_names = []
            weakness = process_elements(char.db.weakness)
            resistance = process_elements(char.db.resistance)
            if not weakness:
                weakness = "None"
            if not resistance:
                resistance = "None"
            for mode in char.get_all_armors():
                all_armors_names.append(mode.db_name)
            focuses = char.db.focuses
            discern, aim, athletics, force, mechanics, medicine, computer, stealth, heist, convince, presence, arcana= char.get_skills()
            border = "________________________________________________________________________________"
            line1 = "Name: %s" % (name)
            line2 = "Templates: %s" % (types)
            line3 = "Current Mode: %s " % (armor)
            line35 = "Available Armors: %s" % str(all_armors_names)
            line4= (f" POW: {num_to_line(pow)}\n DEX: {num_to_line(dex)}\n TEN: {num_to_line(ten)}\n CUN: {num_to_line(cun)}\n EDU: {num_to_line(edu)}\n CHR: {num_to_line(chr)}\n AUR: {num_to_line(aur)}")
            #line5 = "Skills go here"
            line5 = (f"\n Discern:   {num_to_skill(discern)}         Size: {size}\n Aim:       {num_to_skill(aim)}         Speed: {speed}\n Athletics: {num_to_skill(athletics)}         Strength: {strength} \n Force:     {num_to_skill(force)} \n Mechanics: {num_to_skill(mechanics)}         Weakness: {weakness}\n Medicine:  {num_to_skill(medicine)}         Resistance: {resistance}\n Computer:  {num_to_skill(computer)}\n Stealth:   {num_to_skill(stealth)}\n Heist:     {num_to_skill(heist)}\n Convince:  {num_to_skill(convince)}\n Presence:  {num_to_skill(presence)}\n Arcana:    {num_to_skill(arcana)}")
            
            line6 = "\nCapabilities: %s" % (cap)
            line7 =  "Size: %s Speed: %s Strength: %s"% (size,speed, strength)
            line8 = "Weakness: %s Resistance: %s" % (weakness, resistance)
            line9 = "Focuses: %s" % (focuses)

            sheetmsg = (border + "\n\n" + line1 + "\n" + line2 + "\n" + line3 + "\n" + line35 + "\n" + line4  + "\n" + line5 + "\n" + line6 + "\n" + line9 + "\n\n" + border + "\n")
            caller.msg(sheetmsg)
            return


class CmdCheckWeapons(MuxCommand):

        """
        List my weapons.

        Usage:
          weapons
          weapons/verbose

        Displays a list of your current weapons.

        If you choose weapons/verbose, it will show the weapons
        plus any short description of each that is set. Otherwise,
        it shows just a short list telling you the names and 
        types of weapons you have available.

        See help wdesc for how to set short descs onto your weapons.
        """

        key = "weapons"
        aliases = ["+weapons", "weapon", "+weapon"]
        locks = "perm(Player)"
        help_category = "General"

        def func(self):
            """implements the actual functionality"""
            caller = self.caller
            switches = self.switches

            # if I'm staff, I can look at other character's arsenal

            if self.args:
                if not caller.check_permstring("builders"):
                    caller.msg("Only staff can check other player's stats. stats to see your own stats.")
                    return
                else:
                    name = self.args.strip()
                    name = name.title()
                    char = caller.search(name, global_search=True) 
                    if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                        self.caller.msg("Character not found.")
                        return

            else:
                name = caller.name
                char = caller


            weapon_list = char.db.weapons

            sheetmsg = ("Weapons: \n")
            for weapon in weapon_list:
                w_name = weapon.db_name
                w_class = weapon.get_db_class_display()
                w_type1 = weapon.get_db_type_1_display()
                '''
                w_class = get_class_text(weapon.db_class)
                w_type1 = get_element_text(weapon.db_type_1)
                '''
                w_type2 = ""
                w_type3 = ""
                w_flag1 = ""
                w_flag2 = ""
                # TODO - you can use get_type_display and not a function, just check all instances
                if weapon.db_type_2:
                    w_type2 = get_element_text(weapon.db_type_2)
                if weapon.db_type_3:
                    w_type3 = get_element_text(weapon.db_type_3)
                if weapon.db_flag_1:
                    w_flag1 = get_effect_text(weapon.db_flag_1)
                if weapon.db_flag_2:
                    w_flag2 = get_effect_text(weapon.db_flag_2)

                sheetmsg = (sheetmsg + w_name + ": " + w_class + " " + w_type1 + " " + w_type2 + " " + w_type3 + " " + w_flag1 + " " + w_flag2 + "\n")
                
                if "verbose" in switches:
                    weapon_desc = weapon.db_description
                    sheetmsg += (f" Desc: {weapon_desc}\n")

            #sheetmsg = (weapon_list)
            caller.msg(sheetmsg)
            return

class CmdWeaponDesc(MuxCommand):
        
    """
    Set an optional description for your weapons.

    Usage:
        weapondesc <weapon name>=<desc>

    weapondesc with a name and desc sets a short desc on each weapon.

    This is entirely optional, but can be useful for people who are grabbing
    your weapon via weapon copy, or someone picking up an FC after you.

    Example:
        weapondesc Magnet Missle=A magnet shaped missile that homes on the target.

    An alias for weapondesc is wdesc.

    """

    key = "weapondesc"
    aliases = ["+weapondesc", "wdesc", "+wdesc"]
    locks = "perm(Player)"
    help_category = "General"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        args = self.args

        if not args:
            caller.msg("Describe which weapon?")
            return

        w_name = self.lhs 
        w_desc = self.rhs
        
        if not w_desc:
            caller.msg("Syntax error. Please see help wdesc.")
            return
        
        weapon_check = Weapon.objects.filter(db_name__icontains=w_name)
        my_weapons = caller.db.weapons
            
        # match found. Weapons should have a unique name with no duplicates.
        # this will let anybody who has that weapon redesc the weapon...
        # is that a problem? 
        if not weapon_check:
            caller.msg("That weapon is not in your arsenal.")
            return

        for w in my_weapons:
            if weapon_check[0].id == w.id:                    
                weapon = w
            
        if not weapon:
                #no weapon no attack
                caller.msg("That weapon is not in your arsenal.")
                return
        else:
            weapon.db_description = w_desc
            weapon.save()
            caller.msg(f"Added description to weapon {weapon.db_name}")

                

        return


class CmdCookie(MuxCommand):

    """
    Give a mouse a cookie.
    
    Usage:
       cookie <player>

    This gives a little cookie to a player that you did RP with.
    The cookie is a vote or 'thank you' for roleplay.
    +vote does the same thing as cookie.
    
    Check cookie board leaders with +100check or +monsters.
    """

    key = "cookie"
    aliases = ["+cookie", "vote", "+vote"]
    locks = "perm(Player)"
    help_category = "Rewards"

    def func(self):
        "This performs the actual command"
        caller = self.caller
        if not self.args:
            caller.msg("Give cookie to who?")
            return
        
        # find a player in the db who matches this string
        char_string = self.args.strip()
        char = caller.search(char_string, global_search=True)

        #make sure this is a valid player!
        if not char:
            caller.msg("Character not found.")
            return
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            caller.msg("Character not found.")
            return
        if (caller.db.cookiequota < 1):
            caller.msg("Sorry, you are out of cookies!")
            return
        try:
            caller.msg(f"You give {char.name} a cookie!")
            char.db.cookiecount += 1
            caller.db.cookiequota -= 1
        except ValueError:
            caller.msg("Some error occured.")
            return


class CmdDecompileMe(MuxCommand):

    """
   
    Usage:
        decompile

    This command will provide you with all the personal information you have
    filled out about a character:
    * efinger information
    * personal info files if they exist
    * soundtrack
    * relationships if they exist

    This does not include all of your character's descs: see help mdesc to
    get all of your descs.

    This command is spammy! It's designed to be used if you are about to
    drop a character and want to be sure you keep all your writing.
    You should also be sure to keep any @mail you want to keep.

    """

    key = "decompile"
    aliases = ["+decompile"]
    locks = "perm(Player)"
    help_category = "General"

    def func(self):
        caller = self.caller
        caller.msg("Later this command will actually work!")


class CmdCookieCounter(MuxCommand):

    """
   
    Usage:
        tally

    See how many cookies you have, and how many cookies
    you have to give out for the rest of the week. 

    """

    key = "tally"
    aliases = ["+tally", "checkcookies", "+checkcookies"]
    locks = "perm(Player)"
    help_category = "Rewards"

    def func(self):
        caller = self.caller
        caller.msg("You have %s cookies!" % (caller.db.cookiecount))



class CmdCookiemonsters(MuxCommand):

    """
    Give a mouse a cookie.
    
    Usage:
      100check

      Shows a leaderboard of PCs with 100 cookies or more.
    """
    key = "100check"
    aliases = ["+100check", "monsters", "+monsters"]
    locks = "perm(Player)"
    help_category = "Rewards"

    def func(self):
        self.caller.msg("Wow here's all the people with 100 cookies!")

class CmdCookieBomb(MuxCommand):

    """
    Give a mouse a cookie.
    
    Usage:
      cookiebomb

      This command locked to staff gives a +cookie to everyone
      in the room that is not set +observer.
    """
    key = "cookiebomb"
    aliases = ["+cookiebomb"]
    locks = "perm(Builder)"
    help_category = "Admin"

    def func(self):
        self.caller.msg("You give everybody a cookie!")



class CmdCookieMsg(MuxCommand):

    """
    Set your custom cookie message.
    
    Usage:
      cookiemsg <message>

    This customizes the string that will be sent when you give
    a cookie to another player.
    Please make it clear that this is the purpose of the message
    when you compose your custom cookie message!

    Future update: typing this with no arguments
    shows you your own message.

    """

    key = "cookiemsg"
    aliases = ["+cookiemsg"]
    locks = "perm(Player)"
    help_category = "Rewards"

    def func(self):
        "This performs the actual command"
        if not self.args:
            self.caller.msg("Set the message to what?")
            return
        
        # find a player in the db who matches this string
        player = self.caller.search(self.args)
        if not player:
            return
        char = player
        if not char:
            self.caller.msg("Character not found.")
            return
        try:
            self.caller.msg(f"You give {char.name} a cookie!")
        except ValueError:
            self.caller.msg("Some error occured.")
            return


class CmdShowMyToggles(MuxCommand):
    """
    Show what toggles you have set.
    
    Usage:
      toggles

    A quick glance to see if you have the following toggles set or not:

    * nospoof
    * stagemute
    * observer
    * privacy
    * radio stuff TBD


    """
    key = "toggles"
    aliases = ["+toggles"]
    locks = "perm(Player)"
    help_category = "General"

    def func(self):
        caller = self.caller
        caller.msg("Toggles status:")
        caller.msg(f"NoSpoof: {caller.db.nospoof}")
        caller.msg(f"Stage Mute: {caller.db.stagemute}")
        caller.msg(f"Observer: {caller.db.observer}")
        caller.msg(f"Pose privacy: {caller.db.potprivate}")
        return