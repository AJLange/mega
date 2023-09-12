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
from server.battle import process_elements, process_attack_class, process_effects, get_element_text, get_class_text, get_effect_text

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

    To get basic IC information about a character. Usually set to what is publically 
    known or can be looked up about a character from an IC standpoint, including their 
    reputation and known abilities.

    Players can fill these out themselves, but staff has a right to double-check this 
    information for accuracy. You may fill out as much or as little of your +efinger as 
    you like, depending on what can be ICly known or interesting to share.
    
    """
    key = "efinger"
    aliases = ["+efinger", "+efigner", "efigner", "info", "+info"]
    lock = "cmd:all()"
    help_category = "General"

    def func(self):
        "This performs the actual command"
        if not self.args:
            self.caller.msg("EFinger who?")
            return

        caller = self.caller
        char_string = self.args.strip()
        char = self.caller.search(char_string, global_search=True)
        if not char:
            self.caller.msg("Character not found.")
            return
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Character not found.")
            return
        
        
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
            alias, prefemail, discord, rptimes, voice, altchars, info = char.get_ocfinger()
            gender = char.db.gender

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
        locks = "perm(Player))"
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
            line4= "POW: %s, DEX: %s, TEN: %s, CUN: %s, EDU: %s, CHR: %s, AUR: %s"  % (pow, dex, ten, cun, edu, chr, aur)
            #line5 = "Skills go here"
            line5 = "Discern: %s, Aim: %s, Athletics: %s Force: %s, Mechanics: %s, Medicine: %s, Computer: %s, Stealth: %s , Heist: %s , Convince: %s, Presence: %s, Arcana: %s"  % (discern, aim, athletics, force, mechanics, medicine, computer, stealth, heist, convince, presence, arcana)
            line6 = "Capabilities: %s" % (cap)
            line7 =  "Size: %s Speed: %s Strength: %s"% (size,speed, strength)
            line8 = "Weakness: %s Resistance: %s" % (weakness, resistance)
            line9 = "Focuses: %s" % (focuses)

            sheetmsg = (border + "\n\n" + line1 + "\n" + line2 + "\n" + line3 + "\n" + line35 + "\n" + line4  + "\n" + line5 + "\n" + line6 + "\n" + line7 + "\n" + line8 + "\n" + line9 + "\n\n" + border + "\n")
            caller.msg(sheetmsg)
            return


class CmdCheckWeapons(MuxCommand):

        """
        List my weapons.

        Usage:
          weapons

        Displays a list of your current weapons.
        """

        key = "weapons"
        aliases = ["+weapons"]
        locks = "perm(Player))"
        help_category = "General"

        def func(self):
            """implements the actual functionality"""
            caller = self.caller

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
                w_class = get_class_text(weapon.db_class)
                w_type1 = get_element_text(weapon.db_type_1)
                w_type2 = ""
                w_type3 = ""
                w_flag1 = ""
                w_flag2 = ""
                if weapon.db_type_2:
                    w_type2 = get_element_text(weapon.db_type_2)
                if weapon.db_type_3:
                    w_type3 = get_element_text(weapon.db_type_3)
                if weapon.db_flag_1:
                    w_flag1 = get_effect_text(weapon.db_flag_1)
                if weapon.db_flag_2:
                    w_flag2 = get_effect_text(weapon.db_flag_2)

                sheetmsg = (sheetmsg + w_name + ": " + w_class + " " + w_type1 + " " + w_type2 + " " + w_type3 + " " + w_flag1 + " " + w_flag2 + "\n")

            #sheetmsg = (weapon_list)
            caller.msg(sheetmsg)
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
    locks = "perm(Player))"
    help_category = "Rewards"

    def func(self):
        "This performs the actual command"
        if not self.args:
            self.caller.msg("Give cookie to who?")
            return
        
        # find a player in the db who matches this string
        char_string = self.args.strip()
        char = self.caller.search(char_string, global_search=True)

        #make sure this is a valid player!
        if not char:
            self.caller.msg("Character not found.")
            return
        if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
            self.caller.msg("Character not found.")
            return    
        try:
            self.caller.msg(f"You give {char.name} a cookie!")
            char.db.cookiecount += 1
        except ValueError:
            self.caller.msg("Some error occured.")
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
    locks = "perm(Player))"
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
    locks = "perm(Player))"
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
    locks = "perm(Player))"
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
    locks = "cmd:all()"
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
    locks = "perm(Player))"
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
    * radio stuff TBD


    """
    key = "toggles"
    aliases = ["+toggles"]
    locks = "perm(Player))"
    help_category = "General"

    def func(self):
        caller = self.caller
        caller.msg("Toggles status:")
        caller.msg(f"NoSpoof: {caller.db.nospoof}")
        caller.msg(f"Stage Mute: {caller.db.stagemute}")
        caller.msg(f"Observer: {caller.db.observer}")
        caller.msg(f"Pose privacy: {caller.db.potprivate}")
        return