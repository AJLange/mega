'''
Stages code. This is like Places, but not.

We want stages to broadcast, to organize big scenes, rather
than be private stages that don't broadcast out, so everything
should hit the main room.

'''

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.utils import list_to_string
from typeclasses.cities import Stage
from evennia import default_cmds, create_object
from evennia.utils import search
from evennia.utils import utils, create
from server.utils import sub_old_ansi
from evennia.utils.utils import inherits_from
from evennia import ObjectDB





# ------------------------------------------------------------
# Commands defined for stages
# ------------------------------------------------------------


class CmdMakeStage(MuxCommand):
    """
    Create a stage.

    Usage:
        makestage <name of stage>
        makestage <name> = <desc>
        eg
        makestage Dinosaur Tank
        makestage Dinosaur Tank = <stage desc>

    A stage is an object that can be 'joined.'
    It does not behave like a room; it simply shows a relative location 
    of players to ease in the creation of setpieces that may have 
    multiple sub-locations.

    Optionally, you can desc the stage when creating it, or use the 
    setstage command to desc after the fact.

    All poses done inside a stage append the name of the stage to the 
    front of the pose, for ease of readability.

    Stages are typically temporary, so use +clearstage to remove them
    when you are done using them.

    """

    key = "makestage"
    alias = "+makestage"
    locks = "perm(Player)"
    help_category = "Scenes"
    
    new_obj_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
        )
    
    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args

        if not args:
            caller.msg("Syntax: stage <name of stage>")
            return


        if not caller.check_permstring("builders"):
            caller.db.stagequota = caller.db.stagequota -1
        
        #subtract from my available quota and make an object with no special properties.

        if caller.db.stagequota < 1:
            caller.msg("Sorry, you can't make any more stages.")
            return

        if not self.args:
            caller.msg("Usage: makestage <Name of item>")
            return

        stagename = self.lhs
        desc = self.rhs
        new_obj = create_object("cities.Stage",key=stagename,location=caller.location,locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)

        lockstring = self.new_obj_lockstring.format(id=caller.id)
        new_obj.locks.add(lockstring)
        new_obj.db.owner = caller

        if desc:
            desc = sub_old_ansi(desc)
            new_obj.db.desc = desc
        
        if new_obj:
            caller.msg("You created the stage %s." % str(new_obj))
        else:
            caller.msg("Can't create %s." % str(new_obj))
            return

class CmdSetStage(MuxCommand):
    """
    Describe a stage.

    Usage:
      setstage <name>=Description
      eg
      setstage Dinosaur Tank=It's the Dinosaur Tank!

    Describe a stage. This description will be visible when
    looking at the stage, or when entering it. Describing 
    a stage is optional.

    """

    key = "setstage"
    alias = "+setstage"
    locks = "perm(Player)"
    help_category = "Scenes"
    

    def func(self):
        """Implements command"""
        caller = self.caller
        args = self.args

        if not args:
            caller.msg("Syntax: stage <number>=<Desc>")
            return

        obj_desc = args.split("=")
        if len(obj_desc) < 1:
            caller.msg("Syntax error: use setstage <obj>=<desc>")
            return
        else:
            description = sub_old_ansi(obj_desc[1])
            obj = ObjectDB.objects.object_search(obj_desc[0], typeclass=Stage)
            if not obj:
                caller.msg("No object by that name was found.")
                return
            if not obj[0].db.owner == caller:
                if not caller.check_permstring("builders"):
                    caller.msg("That object is not yours.")
                    return
            obj[0].db.desc = ("\n" + description + "\n")
            caller.msg("You update the desc of: %s" % str(obj[0]))


class CmdClearStage(MuxCommand):
    """
    Clears away all the stages in the room which were made
    by you.

    Usage:
      clearstage
      clearstage <name>
      clearstage Dinosaur Tank

    This is to be used when you are done with a scene that used
    stages and want to clean up after yourself.

    Clearstage on its own clears all stages in a location.
    Clearstage with an argument looks for a stage named 'arg' anywhere
    and tries to delete that stage.

    """

    key = "clearstage"
    aliases = ["+clearstage", "clearstages","+clearstages"]
    locks = "perm(Player)"
    help_category = "Scenes"
    
    def remove_stage(self, stage):
        for occupant in stage.db.occupants:
            occupant.db.stage = 0
            occupant.msg(f"You were removed from stage {stage}.")
        #delete it
        stage.delete()
        

    def func(self):
        """Implements command"""
        caller = self.caller
        location = caller.location
        args = self.args

        if not args:
            #for all stages in this location
            stages = Stage.objects.filter(db_location=location)
            for stage in stages:
                #check for permissions
                if stage.db.owner == caller:
                    self.remove_stage(stage)
                    caller.msg(f"Removed {stage}")
                    #if the player is not a staffer, return a stagequota
                    if not caller.check_permstring("builders"):
                        caller.db.stagequota = caller.db.craftquota +1
                    
        else:
            stage = Stage.objects.filter(args)
            errmsg = "Couldn't find that stage."
            if not stage:
                caller.msg(errmsg)
                return
            else:
                if stage.db.owner != caller:
                    caller.msg(errmsg)
                else:
                    self.remove_stage(stage)
                    caller.msg(f"Removed {stage}.")
                    #if the player is not a staffer, return a stagequota
                    if not caller.check_permstring("builders"):
                        caller.db.stagequota = caller.db.craftquota +1
            



class CmdStageSelect(MuxCommand):
    """
    Enters a particular stage.

    Usage:
        select <stage name>

    Enters a stage in the room.
    
    Posing while in a stage will append the location of the 
    stage to your pose. This is for organizing plot scenes 
    that technically take place in more than one location.

    To leave, use 'depart'.
    """

    key = "select"
    alias = "+select"
    locks = "perm(Player)"
    help_category = "Scenes"

    def func(self):
        """Implements command"""
        caller = self.caller
        location = caller.location
        stages = Stage.objects.filter(db_location=location)
  
        
        args = self.args

        if not args:
            caller.msg("Usage: select <stage name>")
            caller.msg("To see a list of stages: stages")
            return
        
        if len(stages) < 1:
            caller.msg("This room has no stages.")
            return
        
        args = args.lstrip()

        my_stage = Stage.objects.filter(db_key__icontains=args, db_location=location)

        if not my_stage:
            caller.msg("No match for that stage was found.")
            return
        if len(my_stage) > 1:
            caller.msg("Multiple matches, be more specific.")
            return

        if caller.db.stage:
            caller.msg(f"You leave {caller.db.stage}.")

        # found a match, so set that stage.
        name = my_stage[0].db_key
        caller.db.stage = my_stage[0]
        my_stage[0].db.occupants.append(caller)

        # I am now in a stage.

        caller.location.msg_contents(f"{caller} moves to {name}.", from_obj=caller)


class CmdListStages(MuxCommand):
    """
    Lists stages in current room.

    Usage:
        stages

    Lists all the stages in the current room that you can enter,
    and which players are in which stage.
    
    If there any stages within the room, the 'join' command will 
    be available. 
    
    Posing while in a stage will append the location of the stage 
    to your pose. This is for organizing plot scenes that technically 
    take place in more than one location. There's no coded limit to how
    many people can be in the same stage, but scene-runners may set
    soft limits.

    To leave a stage, use the command 'depart.' You can also enter
    a different stage.
    
    """

    key = "stages"
    alias = "+stages"
    locks = "perm(Player)"
    help_category = "Scenes"

    def func(self):
        """Implements command"""
        caller = self.caller
        location = caller.location

        stages = Stage.objects.filter(db_location=location)

    
        if len(stages) < 1:
            caller.msg("No stages found.")
            return

        caller.msg("|wStages here:|n")
        caller.msg("|w------------|n")

        for num in range(len(stages)):
            p_name = stages[num].key
            caller.msg(p_name)
            occupants = stages[num].db.occupants
            if len(occupants) > 0:
                # get names
                names = [ob.name for ob in occupants if ob.access(caller, "view")]
                caller.msg("-Occupants: %s" % list_to_string(names))


class CmdDepart(MuxCommand):
    """
    Leaves your current stage. 

    Usage:
        depart

    Leaves your current stage. Logging out or disconnecting will
    cause you to leave automatically. To see available stages,
    use 'stages'. To join a stage, use 'join'.
    """

    key = "depart"
    locks = "perm(Player)"
    help_category = "Scenes"

    def func(self):
        """Implements command"""
        caller = self.caller
        stage = caller.db.stage
        location = caller.location

        if not caller.db.stage:
            caller.msg("You are not in a stage.")
            return

        my_stage = Stage.objects.filter(db_key__icontains=stage, db_location=location)
        stage_name = my_stage[0].db_key
        stage.db.occupants.remove(caller)
        caller.db.stage = 0

        #take me out of the list of stage occupants

        caller.msg(f"You leave {stage_name}.")


class CmdStageMute(MuxCommand):
    """
    Mutes stages you aren't in.

    Usage:
        +stagemute

    Stages are sub-locations meant to split up RP during plot scenes.
    If you are in a stage, you may want to mute the output of stages
    you are not in to cut down on screen spam. To do this, use the
    +stagemute command.

    This is a toggle; to turn off stagemute, just use the +stagemute 
    command again. If you leave the stage you are in, stages
    automatically unmute.
    """

    key = "stagemute"
    alias= "+stagemute"
    locks = "perm(Player)"
    help_category = "Scenes"
    # characters used for poses/emits

    def func(self):
        """Implement this command"""
        caller = self.caller
        if not caller.db.stagemute:
            #not muted, so toggle mute
            caller.db.stagemute = True
            caller.msg("You turn on stage muting.")
            return
        else:
            #normal functionality
            caller.db.stagemute = False
            caller.msg("You turn off stage muting.")
            return
       



'''
notes here on player quotas:
10 items
10 personal rooms
10 stages

per player character.
Pets can only be created by staff for now (may change later)

'''

