"""
Scenes

Commands related to the autologger and scene scheduler.
Pose Order Tracker commands should also live here.


"""
from math import floor
#from typing import AwaitableGenerator
from evennia.server.sessionhandler import SESSIONS
import time
import re
from evennia import ObjectDB, AccountDB
from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import utils, create, evtable, make_iter, inherits_from, datetime_format
from evennia.comms.models import Msg
from world.scenes.models import Scene, LogEntry
from typeclasses.rooms import Room
from django.conf import settings

from datetime import datetime

#default beats for sequences, may change this later
BEATS_MULTI = 3

# from evennia import default_cmds

def prune_sessions(session_list):
    # This function modifies the display of "who" and "+pot" so that, if the same player is connected from multiple
    # devices, their character name is only displayed once to avoid confusion. Admin still see all connected sessions.
    session_accounts = [session.account.key for session in session_list]  # get a list of just the names

    unique_accounts = set(session_accounts)
    positions = []

    for acct in unique_accounts:
        # finds positions of account name matches in the session_accounts list
        account_positions = [i for i, x in enumerate(session_accounts) if x == acct]

        # add the position of the account entry we want to the positions list
        if len(account_positions) != 1:
            positions.append(account_positions[-1])
        else:
            positions.append(account_positions[0])

    positions.sort()  # since set() unorders the initial list and we want to keep a specific printed order
    pruned_sessions = []

    for pos in positions:
        pruned_sessions.append(session_list[pos])

    return pruned_sessions

def add_participant_to_scene(character, scene):
    '''
    Given a character, checks the given scene's participants for that character and, if
    NOT present, adds the character as a participant to the scene.
    '''

    if scene.participants.filter(pk=character.id):
        return

    scene.participants.add(character)

# Borrowing these functions from SCSMUSH autologger with permission
# text replacement function stolen from https://stackoverflow.com/questions/919056/case-insensitive-replace
def ireplace(old, repl, text):
    # This function is used in highlight_names to replace names: it is not case sensitive but maintains case.
    return re.sub('(?i)'+re.escape(old), lambda m: repl, text)


def highlight_names(source_character, in_string, self_color, others_color):
    # This function is used in tailored_msg.
    if self_color is None:
        self_color = "550"

    if others_color is None:
        others_color = "055"

    # find all characters in current room
    char_list = source_character.location.contents_get(exclude=source_character.location.exits)
    name_list = []
    self_name_list = [] # These are necessary to color the source character's name separately
    full_list = []
    self_full_list = []

    # generate a list of all names of said characters, including aliases
    for character in char_list:
        name_list.append(character.key)
        name_list += character.aliases.all()
        if character == source_character:
            self_name_list.append(character.key)
            self_name_list += character.aliases.all()

    # generate a list of all occurrences of the name in the input string. This will allow us to print the names
    # exactly as they were written, without overriding case
    for name in name_list:
        full_list += re.findall(re.compile(re.escape(name), re.IGNORECASE), in_string)
        if name in self_name_list:
            self_full_list += re.findall(re.compile(re.escape(name), re.IGNORECASE), in_string)

    out_string = in_string
    # for each of the names in the list, replace the string with a colored version
    for name in full_list:
        if name in self_full_list:
            out_string = ireplace(name, "|" + self_color + name + "|n", out_string)
        else:
            out_string = ireplace(name, "|" + others_color + name + "|n", out_string)

    return out_string

def tailored_msg(caller, msg):
    # the point of this function is to
    # 1. Get a list of character objects in the room
    # 2. For each character, check whether names should be colored
    # 3. And custom color the names so that the receiving character's name is highlighted a different color
    char_list = caller.location.contents_get(exclude=caller.location.exits)
    # for char in char_list:
    #     caller.msg("{0}".format(char))

    for character in char_list:
        everyone_else = caller.location.contents_get(exclude=caller.location.exits)
        everyone_else.remove(character)
        # for char in everyone_else:
        #     caller.msg("{0}".format(char))
        # caller.msg("pose_colors_self for {0} is {1}".format(character, character.db.pose_colors_self))
        # caller.msg("pose_colors_others for {0} is {1}".format(character, character.db.pose_colors_others))
        # caller.msg("pose_colors_on for {0} is {1}".format(character, character.db.pose_colors_on))

        if character.db.pose_colors_on:
            caller.location.msg_contents(text=(highlight_names(character, msg, character.db.pose_colors_self,
                                                                    character.db.pose_colors_others),
                                                    {"type": "pose"}),
                                              exclude=everyone_else,
                                              from_obj=caller)
        else:
            caller.location.msg_contents(text=(msg, {"type": "pose"}),
                                              exclude=everyone_else,
                                              from_obj=caller)
    return


class CmdPot(MuxCommand):
    """

    View the pose tracker (pot). 
    
    Usage:
      +pot
      +pot/last 
      +pot/last <name>
      +pot/since <name>
      +pot/scene
      +pot/scene <sceneset>
      +pot/privacy
      +pot/observer
    
    The pose tracker displays the name, time connected, time idle, and 
    time since last posed of every character in the room, ordered starting 
    with whomever posed longest ago. Thus, during an ongoing scene, the 
    person whose turn it is to pose will appear at the top of the list.
    Those who have not posed are listed below all those who have.
    To signify that you are leaving an ongoing scene, type +observe
    to reset your pose timer and move to the bottom (see "help observe").

    +pot will display the last combat action a player was involved in along with 
    their LE condition. 

    The +pot/last <Name> command displays the given person's last pose    
    unless they have +pot/privacy toggled on.                                     
    The +pot/last command will display, in order of oldest to newest, all 
    the poses currently stored in the room.                                       
    The +pot/since <Name> command will display, in order of oldest to     
    newest, the pose of the given person and everyone who has posed since they    
    did.

    +pot/scene is used to pull up a scene set pose for late arrivals. It can be
    set by a scene runner using +pot/scene.

    +pot/privacy and +pot/observer means your poses will not be stored. Use 
    +pot/privacy if you are in a private scene you do not want autologged. 
    Use +pot/observer to indicate you are just observing and not participating
    in the scene. 

    See also help +observer and help +toggles.

    TODO: Not sure if any of this functionality actually works.

    """

    key = "+pot"
    aliases = ["pot"]
    locks = "cmd:all()"

    # this is used by the parent
    #account_caller = True

    def func(self):

        switches = self.switches
        args = self.args
        caller = self.caller

        if "privacy" in switches:
            if caller.db.potprivate:
                caller.db.potprivate = False
                caller.msg("Privacy Off: You are now saving your poses in +pot.")
                return
            else:
                caller.db.potprivate = True
                caller.db.lastpose = ""
                caller.msg("Privacy On: +pot will not track your poses.")
                return

        if "observer" in switches:
            if caller.db.observer:
                caller.location.msg_contents(
                "|y<SCENE>|n {0} is no longer an observer.".format(self.caller.name))
                caller.db.observer = False
                return
            else:
                caller.set_pose_time(0.0)
                caller.db.observer = True
                caller.db.lastpose = ""
                caller.msg("Entering observer mode.")
                caller.location.msg_contents(
                "|y<SCENE>|n {0} is now an observer.".format(self.caller.name))
                return

        if "scene" in switches:
            if args:
                caller.location.scenepose = args
                caller.location.sceneset = caller
            else:
                if not caller.location.scenepose:
                    caller.msg("No Scene pose set")
                    return
                caller.msg(f"Scenepose set by: {caller.location.sceneset}/n{caller.location.scenepose}")
                return
        
        """
        Get all connected accounts by polling session.
        """

        all_sessions = SESSIONS.get_sessions()

        all_sessions = sorted(all_sessions, key=lambda o: o.account.character[0].get_pose_time()) # sort by last posed time
        pruned_sessions = prune_sessions(all_sessions)

        if "last" in switches:
            #get all poses
            
            if args: 
                #is this a real present person?
                char = caller.search(args, global_search=False)
                if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                    caller.msg("Character not found.")
                    return
                caller.msg(f"{char.name}'s last pose: \n{char.db.lastpose}\n")
                return
            else:
                #list all the poses
                pose_list = []
                poses = ""
                for session in all_sessions:
                    pose_list.append(session.db.lastpose)
                    poses += (f"{session.db.name}'s last pose: \n{session.db.lastpose}\n")

                caller.msg(poses)
                return

        if "since" in switches:

            #get all poses            
            if args: 
                #is this a real present person?
                char = caller.search(args, global_search=False)
                if not inherits_from(char, settings.BASE_CHARACTER_TYPECLASS):
                    caller.msg("Character not found.")
                    return
                
                #list all the poses since that person
                pose_list = []
                poses = ""
                
                for session in all_sessions:
                    if session.get_pose_time() < args.get_pose_time():
                        pose_list.append(session.db.lastpose)
                        poses += (f"{session.db.name}'s last pose: \n{session.db.lastpose}\n")

                caller.msg(poses)
                return

        table = self.styled_table(
            "|wCharacter",
            "|wIdle",
            "|wLast posed",
            "|wLast action",
            "|wCondition"
        )

        old_session_list = []

        for session in pruned_sessions:
            if not session.logged_in:
                continue

            puppet = session.get_puppet()
            delta_cmd = time.time() - session.cmd_last_visible
            delta_pose_time = time.time() - puppet.get_pose_time()


            '''
            SCS timed out sessions longer than an hour.
            M3 can sometimes be slower, so I'll give you 2.
            '''
            if delta_pose_time > 7200:
                old_session_list.append(session)
                continue
            

            if puppet.location == self.caller.location:
                # logic for setting up pose table
                table.add_row(puppet.key,
                              utils.time_format(delta_cmd, 1),
                              utils.time_format(delta_pose_time, 1))

        for session in old_session_list:
            puppet = session.get_puppet()
            delta_cmd = time.time() - session.cmd_last_visible
            delta_conn = time.time() - session.conn_time


            # Changes display depending on if someone has set themselves as an observer or not.
            if puppet.location == self.caller.location:
                if puppet.db.observer == True:
                    table.add_row("|y" + puppet.key + " (O)",
                                  utils.time_format(delta_cmd, 1),
                                  "-")
                else:
                    table.add_row(puppet.key,
                                  utils.time_format(delta_cmd, 1),
                                  utils.time_format(delta_pose_time, 1))
    
        # no valid switches, just return table
        caller.msg(table)
        return

class CmdObserve(MuxCommand):
    """
        Enter observer mode. 
        
        Usage:
          +observe

        This signifies that you are observing, and not participating, 
        in a scene. In +pot, you will be displayed at the bottom of 
        the list with an "(O)" before your name. If you have previously 
        posed, your pose timer will also be reset.

        If your character is leaving an ongoing scene, +observe
        will help to  prevent anyone accidentally waiting on a pose
        from you.
        
    """

    key = "observe"
    aliases = ["+observe", "observer", "+observer"]
    locks = "cmd:all()"

    def func(self):

        caller = self.caller
        if caller.db.observer:
            caller.location.msg_contents(
            "|y<SCENE>|n {0} is no longer an observer.".format(self.caller.name))
            caller.db.observer = False
            return
        else:
            caller.set_pose_time(0.0)
            caller.db.observer = True
            caller.msg("Entering observer mode.")
            caller.db.lastpose = ""
            caller.location.msg_contents(
                "|y<SCENE>|n {0} is now an observer.".format(self.caller.name))
            return


class CmdSceneSched(MuxCommand):
    """
    Syntax: +scenes (+tp, +scene, +schedule)                                      
        +scene/add <Month>/<Day> <Time> <Title>=<Description>                 
        +scene/del <Month>/<Day>                                              
                                                                              
        The first command displays a list of scheduled scenes. More than one a
day can be stored. Clicking on the 'title' displayed, if you have a hyperlink 
capable client, will read the board post with further details on the scene.   
Further, you can click on the author's name to pull up their +finger and if   
the +scene has had a room location set, once that room has had +pot/port      
turned on, the location becomes a way to teleport to the room.                
                                                                              
        The next command will add your scene to the database along with       
posting it to the Scene Announcements board. +Scene/add operates using the    
number for a month. An example of the command would be:

        +scene/add 2/13 7 PM This Is A Sample Title=This is a sample post.    
        +scene/add 10/31 7:30 Another Sample=Yes PM is optional.              
                                                                              
        The +scene/del command will remove the Month/Date entry you made.     
                                                                              
        The +scenes list should be configured to display in your current
        time zone (todo)
    """

    key = "+scenes"
    aliases = ["scenes", "scene", "+scene", "+tp", "tp", "+schedule" , "schedule", "when", "+when"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        if not self.switches:
            caller.msg("todo: the scene list goes here.")
            return

        elif "add" in self.switches:
            # Add scene
            event = Scene.objects.create(
                name='Unnamed Event',
                start_time=datetime.now(),
                description='Placeholder description of scene plz change k thx bai',
                location=caller.location,
            )
            caller.msg("DEBUG: this event has the following information:\nname = {0}\ndescription = {1}\nlocation = {2}\nid = {3}".format(event.name, event.description, event.location, event.id))

            # caller.location.db.event_id = event.id

            return

        elif "del" in self.switches:
            
            if not self.args:
                caller.msg("Delete which scene?")
            return

            # remove the scene matched by id
            # in the future, we will allow people to edit scenes, so this may be refactored.


class CmdEvent(MuxCommand):
    """
    The +event command is used to log scenes.
    Usage:
            +event/start: Create a scene and begin logging poses in the current room.
            +event/stop: Stop the log currently running in the room.
            +event/info: Display the current log's ID number, name, etc.
            +event/name [string]: Set the current log's name as [string].
            +event/desc [string]: Set the current log's desc as [string].
    """

    key = "+event"
    aliases = ["event", "@event"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        if not self.switches:
            caller.msg("You must add a switch, like '+event/start' or '+event/stop'.")
            return

        elif "start" in self.switches:
            # Make sure the current room doesn't already have an active event, and otherwise mark it
            if caller.location.db.active_event:
                caller.msg("There is currently an active event running in this room already.")
                return
            caller.location.db.active_event = True
            event = Scene.objects.create(
                name='Unnamed Event',
                start_time=datetime.now(),
                description='Placeholder description of scene plz change k thx bai',
                location=caller.location,
            )

            caller.msg("DEBUG: this event has the following information:\nname = {0}\ndescription = {1}\nlocation = {2}\nid = {3}".format(event.name, event.description, event.location, event.id))

            caller.location.db.event_id = event.id

            self.caller.location.msg_contents("|y<SCENE>|n A log has been started in this room with scene ID {0}.".format(event.id))
            return

        elif "stop" in self.switches:
            # Make sure the current room's event hasn't already been stopped
            if not caller.location.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            # Find the scene object that matches the scene/event reference on the
            # location.
            try:
                events = Scene.objects.filter(id=caller.location.db.event_id).get()
            except Exception as original:
                raise Exception("Found zero or multiple Scenes :/") from original

            # Stop the Room's active event by removing the active event attribute.
            Scene.objects.filter(id=caller.location.db.event_id).update(end_time=datetime.now())
            self.caller.location.msg_contents("|y<SCENE>|n A log has been stopped in this room with scene ID {0}.".format(events.id))
            del caller.location.db.active_event
            return

        elif "info" in self.switches:
            # First, check that there is a log running.
            if not caller.location.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            # Find the scene object that matches the scene/event reference on the
            # location.
            try:
                events = Scene.objects.filter(id=caller.location.db.event_id).get()
            except Exception as original:
                raise Exception("Found zero or multiple Scenes :/") from original

            caller.msg("This event has the following information:\nName = {0}\nDescription = {1}\nLocation = {2}\nID = {3}".format(events.name, events.description, events.location, events.id))

        elif "name" in self.switches:
            # First, check that there is a log running.
            if not caller.location.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            # Then, check that the user has inputted a string.
            if not self.args:
                caller.msg("Name the log what?")
                return

            # Find the scene object that matches the scene/event reference on the
            # location.
            try:
                events = Scene.objects.filter(id=caller.location.db.event_id).get()
            except Exception as original:
                raise Exception("Found zero or multiple Scenes :/") from original

            Scene.objects.filter(id=caller.location.db.event_id).update(name=self.args)
            caller.msg("Scene name set.")

        elif "desc" in self.switches:
            # First, check that there is a log running.
            if not caller.location.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            # Then, check that the user has inputted a string.
            if not self.args:
                caller.msg("Name the log description what?")
                return

            # Find the scene object that matches the scene/event reference on the
            # location.
            try:
                events = Scene.objects.filter(id=caller.location.db.event_id).get()
            except Exception as original:
                raise Exception("Found zero or multiple Scenes :/") from original

            Scene.objects.filter(id=caller.location.db.event_id).update(description=self.args)
            caller.msg("Scene description set.")


class CmdSequenceStart(MuxCommand):
    """
    This command declares a Sequence.
    A Sequence is used to indicate an open-GMed scene that contains
    action components but is not a direct combat or duel.

        Usage:
            +sequence/start <optional number>
            +sequence/stop
            +sequence/gm <name>
            +sequence/stepdown
            +sequence/status or +sequence
            +sequence/set <number>

    When you initiate a Sequence, you're setting yourself as a GM 
    in that scene. You can appoint a co-GM by using +sequence/gm <name>
    +sequence/stepdown will turn off your GM flag (if you are done, 
    or want to pass off the GMing role to someone else while still
    leaving the sequence active).

    Each Sequence has a number of beats, multipled by the number of protagonists 
    in the scene (people you're up against). A beat is essentially the HP of 
    the challenge at hand, however it is resolved.  The default number of
    beats is 3 times the amount of adversarial players involved. Players set 
    +observer or appointed GM wil not be added to this calculation. If you want 
    to set this to a different value, you can choose that number when you start 
    a sequence. 

    +sequence/status or +sequence views the players, GM list, amount of beats and 
    remaining beats. 

    +sequence/stop ends the sequence for all participants.
    Only a GM in the sequence can do this.

    If you are GMing you can set the active remaining beats on a sequence with 
    +sequence/set. This is at your descretion of the players' success in the 
    sequence, and for now, is set manually.

    For information on how to GM in a Sequence see 'help GMing' (TBD).
 
    """

    key = "+sequence"
    aliases = ["sequence", "sq","+sq"]
    locks = "cmd:all()"


    def count_players(self,room):
            # find all players here
            charlist = ObjectDB.objects.filter(db_typeclass_path=settings.BASE_CHARACTER_TYPECLASS, db_location=room )
            playerlist = []
            for char in charlist:
                if not char.db.gm: 
                    if not char.db.observer:
                        playerlist.append(char)
            return len(playerlist)


    def func(self):
        caller = self.caller
        room = caller.location
        switches = self.switches
        args = self.args

        # if the room has a protector, remind the player to check that.
        if room.db.protector== "Staff" and not not caller.check_permstring("builders"):
            caller.msg("You can't start a sequence event here - it's protected by staff. Ask staff about using this room.")
            return

        if "start" in switches:
            if room.db.protector:
                caller.msg("This room has a protector set, so make sure they were alerted to your scene happening here (+protector).")
            # Make sure the current room doesn't already have an active event, and otherwise mark it
            if room.db.sequence_beats:
                caller.msg("There is currently an active event running in this room already.")
                return
            caller.location.db.active_event = True
            caller.db.gm = True

            # give HP to the sequence by setting it on the room
            if args:
                try:
                    room_beats = int(args)
                except ValueError:
                    caller.msg("Beats should be a single number.")
                    return
            else:
                room_beats = self.count_players(room) * BEATS_MULTI
            
            if not room_beats:
                caller.msg("You can't have a sequence with no players or challenge. Nothing started.")
                return

            room.sequence_beats = room_beats

            room.msg_contents(f"{caller.name} has begun a sequence in this location! The sequence has {room_beats} beats remaining." )
            room.msg_contents(f"If you do not want to be included, set +observer. To see info type +sequence/status." )  
            return

        if "stop" in switches:
            # Make sure the current room's event hasn't already been stopped
            if not room.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            #remove gm flag from anybody who is in this room
            charlist = ObjectDB.objects.filter(db_typeclass_path=settings.BASE_CHARACTER_TYPECLASS)
            for char in charlist:
                char.db.gm = False
            caller.msg("You stop the sequence in this location.")
            room.msg_contents("The sequence event in this location has ended.")       
            
            room.sequence_beats = 0
            return
               
        if "gm" in switches:
            if not args:
                caller.msg("Set who as GM? Please supply a name.")
                return
            co_gm = self.caller.search(args, global_search=False)

            #make sure this is a valid player in the same room
            errmsg = ("Character not found. A co-GM must be in the same location.")
            if not co_gm:
                self.caller.msg(errmsg)
                return
            if not inherits_from(co_gm, settings.BASE_CHARACTER_TYPECLASS):
                self.caller.msg(errmsg)
                return 
            #all checks succeeded
            co_gm.db.gm = True
            return
        
        if "stepdown" in switches:
            if not caller.db.gm:
                caller.msg("You are not an active GM right now.")
                return
            else:
                caller.db.gm = False
                caller.msg("You step down from being GM of this sequence.")
                return
            
        if "set" in switches:
            if not caller.db.gm:
                caller.msg("You are not an active GM right now.")
                return

            if not args:
                caller.msg("Set sequence beats to what number?")
            else:
                try: 
                    beats = int(args)
                except ValueError:
                    caller.msg("Set beats as a whole number.")
                    return
                room.db.sequence_beats = beats
                caller.location.msg_contents(f"{caller.name} advances the sequence! The sequence has {beats} beats remaining." )       
                if (beats <= 0):
                    room.db.sequence_beats = 0
                    caller.location.msg_contents(f"The sequence is resolved!" )
                    caller.msg("If you are active GM, remember to run +sequence/stop to clean up.")
                return

        if not switches or "status" in switches:
            # if no switch provided, assume I'm looking for status and process this
            if not room.db.sequence_beats:
                caller.msg("No active sequence is happening here.")
                return
            
            text = ("Sequence Status: \n")
            text += ("GM:")
            # find all players here
            charlist = ObjectDB.objects.filter(db_typeclass_path=settings.BASE_CHARACTER_TYPECLASS, db_location=room )
            playerlist = []
            #hacky solution for now, but it works
            for char in charlist:
                if char.db.gm: 
                    text += (f" {char}")
                else:
                    if not char.db.observer:
                        playerlist.append(char) 
            text += ("\nPlayers:")
            for char in playerlist:
                #all gms and observers were removed above, this is everyone else.
                text += (f" {char}")
 
            text += (f"\nBeats Remaining: {str(room.db.sequence_beats)}")

            caller.msg(text)
            return


class CmdAutolog(MuxCommand):
    """
    This command begins the autologger.
   
    Usage:
        +log/start
        +log/stop

    This begins an auto logger at this location.
    Use +log/stop to turn off autologger.

    Scenes set on calendar with the +scene/schedule command
    are auto-logged automatically.

    This command warns the room about the log starting. 
    Logs created this way are private to the involved players
    by default, but can be made public with a command
    that I'll figure out later.

    """

    key = "+log"
    aliases = ["log"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        if not self.switches:
            caller.msg("You must add a switch, like '+log/start' or '+log/stop'.")
            return

        #this is from the event code, make it actually do the thing at a later time.

        # if the room has a protector, remind the player to check that.

        elif "start" in self.switches:
            # Make sure the current room doesn't already have an active event, and otherwise mark it
            if caller.location.db.active_event:
                caller.msg("There is currently an active event running in this room already.")
                return
            caller.location.db.active_event = True
            event = Scene.objects.create(
                name='Unnamed Event',
                start_time=datetime.now(),
                description='Placeholder description of scene plz change k thx bai',
                location=caller.location,
            )

            caller.msg("DEBUG: this event has the following information:\nname = {0}\ndescription = {1}\nlocation = {2}\nid = {3}".format(event.name, event.description, event.location, event.id))

            caller.location.db.event_id = event.id

            self.caller.location.msg_contents("|y<SCENE>|n A log has been started in this room with scene ID {0}.".format(event.id))
            return

        elif "stop" in self.switches:
            # Make sure the current room's event hasn't already been stopped
            if not caller.location.db.active_event:
                caller.msg("There is no active event running in this room.")
                return

            # Find the scene object that matches the scene/event reference on the
            # location.
            try:
                events = Scene.objects.filter(id=caller.location.db.event_id).get()
            except Exception as original:
                raise Exception("Found zero or multiple Scenes :/") from original

            # Stop the Room's active event by removing the active event attribute.
            Scene.objects.filter(id=caller.location.db.event_id).update(end_time=datetime.now())
            self.caller.location.msg_contents("|y<SCENE>|n A log has been stopped in this room with scene ID {0}.".format(events.id))
            del caller.location.db.active_event
            return
