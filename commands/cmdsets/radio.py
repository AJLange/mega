from evennia.commands.default.muxcommand import MuxCommand
from evennia import default_cmds, create_object, search_object
from evennia.utils import utils, create
from server.utils import sub_old_ansi, color_check
from world.radio.models import Frequency


def get_frequency_index(caller, letter):
    try:
        letter = (letter[0]).upper
    except:
        caller.msg("Frequencies should be letters.")
        return
    i = caller.db.radio_slots.index(letter)
    return i


class CmdRadio(MuxCommand):

    """
    Radio commands.

    Usage:
        +radio
        +radio <Frequency Letter>=<Message>
        +radio <Name>=<Message>
        +radio <Name,Name 2, Name 3, Name n>=<Message>
        +radio/on or +radio/off
        +radio/reset
        +radio/spoof

    The first command will display your radio status. It will display what
    frequencies you have set, what letter they are, the color, title, and name of 
    the channel; along with whether the channel is gagged or not.                 
    
    The second command, when given input such as '+radio B=:waves hello'  
    will transmit a message to everyone on that radio frequency. The command will 
    accept pose (:), semi-pose (;), and standard speaking.

    The third and fourth command will send messages directly to the people
    you listed in a 'tightbeam' message.     

    2way doesn't work yet. See also +2way, tightbeam, saraband, telepath.

    The /on or /off switches turn the radio on or off. Having your radio off 
    means no one can send you radio messages.

    /reset switch clears all your frequencies. Use with caution.
    /spoof toggle toggles radio nospoof. This command will toggle on radio 
    no_spoofing so that when someone @emits on a radio channel, their name is 
    attached to the beginning of the message.    
    """

    key = "radio"
    aliases = ["+radio"]
    locks = "cmd:not pperm(page_banned)"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        switches = self.switches

        if "on" in switches or "off" in switches:
            #turn radio on or off.
            if caller.db.radio_on:
                caller.db.radio_on = False
                caller.msg("Radio off.")
            else:
                caller.db.radio_on = True
                caller.msg("Radio on.")
            return
    
        if "spoof" in switches:
            #turn nospoof on or off.
            if caller.db.radio_nospoof:
                caller.db.radio_nospoof = False
                caller.msg("Radio Nospoof turned off.")
            else:
                caller.db.radio_nospoof = True
                caller.msg("Radio Nospoof turned on.")
            return
        
        if "reset" in switches:
            #reset the radio
            for freq in caller.db.radio_list:
                freq.pop()
            for name in  caller.db.radio_names:
                name.pop()
            for title in caller.db.radio_titles:
                title.pop()
            caller.msg("All radio frequencies cleared.")
            return
        
        
        else:
            #no switches or invalid switch, continue
            try:
                letter = self.lhs
                msg = self.rhs

                letter = str(freq)
                if len(letter) == 1:
                    #one letter, so it's a frequency, else do a 2way
                    i = get_frequency_index(caller,freq)
                    freq = caller.db.radio_list[i]
                    freq_name = caller.db.radio_names[i]
                    freq_title = caller.db.radio_titles[i]
                    freq_colors = caller.db.radio_colors[i]
                    #for all members of this radio frequency
                    for member in freq.db_members:
                        member.msg("Radio Message from frequency A:")
                    #who aren't gagging the channel
                    #am i spoofing? 
                        if msg[0] == "@":
                            #process as spoofed
                            spoof_message = msg[1:]
                            #also check nospoof
                            if member.db.radio_nospoof:
                                full_string = (f"(From {caller.name}): {spoof_message} \n")
                            else:
                                full_string = (spoof_message + "\n")
                            member.msg(full_string)
                            return
                        else:
                            member.msg(f'{caller.name} transmits: "{msg}"')
                            return
                    #TODO: format with reciever's frequency and color
                    #maybe do some processing for interceptors
                    
                    return
                else:
                    receiver_list = freq.strip().split(',')
                    for r in receiver_list:
                        if r.db.radio:
                            if not r.radio_on:
                                caller.msg(f"{r.name}'s radio is turned off.")
                            else:
                                r.msg(f"Tightbeam from {caller.name}: {msg} \n")
                                
                            if len(receiver_list) > 1:
                                r.msg("(Sent to")
                                for s in receiver_list:
                                    r.msg(f"{s.name} )\n")
                    caller.msg(f"Tightbeam to {freq}: {msg} \n")
                    return
            except:
                #no args either, so just return status
                caller.msg("Radio status: to be added")
                return


class CmdFrequency(MuxCommand):

    """
    Stubbing out radio commands

    Usage:
        +freq/set <Letter>=<Number>
        +freq/name <Letter>=<Name>
        +freq/color <Letter>=<Color>
        +freq/total <Number>
        +freq/clear <Letter>
        +freq/reset
        +freq/gag <Letter>
        +freq/who <Letter>
        +freq/swap <Letter>=<Letter>
        +freq/recall <Letter>
        +freq/recall <Letter>=<Number>


    These commands will set various settings on a specific frequency. The 
    SET option will set the letter in +radio to the given frequency number. The   
    NAME option will give the channel a specific name which will show up when you 
    receive radio messages. The TOTAL option gives you more or less frequency slots 
    total, up to 26. 
    
    The CLEAR option will wipe all the settings for the given channel     
    letter. The GAG option will make it so you do not hear messages received on   
    that frequency. The WHO option will display who is currently on a channel and 
    whether they have it gagged or not. The SWAP option will let you switch the   
    settings for two letters between each other. The RECALL option will display   
    either the maximum of 50 lines recall buffer stored from the channel chatter  
    or a given number less than 50.     

    """

    key = "freq"
    aliases = ["+freq"]
    locks = "cmd:all()"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        switches = self.switches
        args = self.args
        errmsg = "Syntax error. See help +freq"

        if "set" in switches:
            #set a frequency            
            if not args:
                caller.msg(errmsg)
                return
            try:
                letter_freq = self.lhs
                num_freq = self.rhs
                num_freq = int(num_freq)
            except:
                caller.msg(errmsg)
                return
            #just one uppercase letter
            letter_freq = (letter_freq[0]).upper
            #check my amount of frequencies
            my_freq_amount = caller.db.radio_channels
            number_converted = ord(letter_freq) - 64
            if my_freq_amount < number_converted:
                caller.msg("You don't have that many frequencies. Try +freq/total.")
                return
            if num_freq > 1000000 or num_freq < 0:
                caller.msg("Frequency numbers must be positive integers 6 digits or less.")
                return
            #does it exist? 
            freq = Frequency.objects.filter(db_freq__iexact=num_freq)
            if not freq:
                #does not exist so create it
                freq = Frequency.objects.create(db_freq = num_freq)

            freq.db_members.add(caller) 
            caller.db.radio_list.append(freq)
            caller.db.radio_names.append("No Name")
            caller.db.radio_slots.append(letter_freq)
            caller.db.radio_titles.append("")
            caller.db.radio_colors.append("|400")
            caller.msg(f"Added you to frequency {num_freq} on slot {letter_freq}.")
            return

        if "name" in switches:
            #name frequency
            if not args:
                caller.msg(errmsg)
                return
            try:
                letter_freq = self.lhs
                name_freq = self.rhs
            except:
                caller.msg(errmsg)
                return
            #just one uppercase letter
            letter_freq = (letter_freq[0]).upper
            #check my amount of frequencies
            my_freq_amount = caller.db.radio_channels
            number_converted = ord(letter_freq) - 64
            if my_freq_amount < number_converted:
                caller.msg("You don't have that many frequencies. Try +freq/total.")
                return
            caller.db.radio_names[i] = name_freq
            caller.msg(f"Set name of Frequency {letter_freq} to {name_freq}.")
            return
        
        if "clear" in switches:
            #clear a frequency
            letter = args
            i = get_frequency_index(caller,letter)
            if not i:
                caller.msg("You don't have that many radio channels.")
                return
            else:
                caller.radio_list.pop(i)
                caller.radio_names.pop(i)
                caller.radio_titles.pop(i)
                caller.radio_colors.pop(i)
                caller.msg(f"Cleared frequency {letter}.")
                return
    
        if "gag" in switches:
            #gag
            letter = args
            i = get_frequency_index(caller,letter)
            if not i:
                caller.msg("You don't have that many radio channels.")
                return
            num_freq = caller.db.radio_list[i]
            freq = Frequency.objects.filter(db_freq__iexact=num_freq)
            if not freq:
                #this shouldn't happen, but...
                caller.msg("Error, contact an admin to debug this.")
                return
            freq.db_gaglist.add(caller)
            caller.msg(f"Now gagging frequency {freq_letter}.")
            #TODO: reset gag list on logout
            return
        
        if "color" in switches:
            # over-ride freq color
            # try getting frequency letter
            letter = self.lhs
            color = self.rhs
            i = get_frequency_index(caller,letter)
            if not i:
                caller.msg("You don't have that many radio channels.")
                return
            # try checking valid color
            if color_check(color) == "invalid":
                caller.msg("Please use a valid color code.")
                return
            # find index of frequency and set.
            caller.db.radio_colors[i] = color
            caller.msg(f"Set color of Frequency {letter} to {color}.")
            return
        
        if "who" in switches:
            #who
            try:
                freq_letter = args
                freq_letter = (freq_letter[0]).upper
            except:
                caller.msg(errmsg)
                return
            i = caller.db.radio_slots.index(freq_letter)
            if not i:
                caller.msg("You don't have that many radio channels.")
                return
            num_freq = caller.db.radio_list[i]
            freq = Frequency.objects.filter(db_freq__iexact=num_freq)
            if not freq:
                #this shouldn't happen, but...
                caller.msg("Error, contact an admin to debug this.")
                return
            message = (f"On radio frequency {freq_letter}: ")
            for c in freq.db_members:
                message += c.name
                message += " "
            caller.msg(message)
            return
    
        if "swap" in switches:
            #name frequency
            return
        
        if "recall" in switches:
            #recall up to 50 messages
            return
        
        if "total" in switches:
            #More total frequencies
            errmsg = "Supply an integer between 1 and 26."
            if not args:
                caller.msg(errmsg)
                return
            try:
                num = int(args)
            except ValueError:
                caller.msg(errmsg)
                return
            if num > 1 and num < 26:
                caller.db.radio_channels = num
            else: 
                caller.msg(errmsg)
                return
            caller.db.radio_channels = num
            caller.msg(f"Set number of radio frequencies to {num}.")
            return
        
        else:
            caller.msg("Invalid switch. See help +freq.")
            return

class CmdFrequencyAdmin(MuxCommand):

    """
    Group leaders and second in commands can set factional radio frequencies
    using this command.

    Usage:
      +freqadmin/update
      +freqadmin/chat <Letter>=<Number>=<Channel Name>
      +freqadmin/secure <Letter>=<Number>=<Channel Name>

    The first command uses the frequencies displayed in +motd and updates 
    your +radio system with those group or team based frequencies.              
    
    The +freq/chat and +freq/secure commands sets up the +motd's          
    group-based frequencies. These commands will also auto-update the +radio's  
    of everyone in the group so that everyone stays on the same frequency. The    
    /secure option makes the channel harder to crack; groups should only have   
    one secure channel.                                                           

    """

    key = "freqadmin"
    aliases = ["+freqadmin"]
    # might have to set this to player only
    locks = "cmd:all()"
    help_category = "Radio"

    def func(self):
        """Implement function using the Msg methods"""

        # this is a MuxCommand, which means caller will be a Character.
        caller = self.caller
        return
    
'''
============================= +Radio Quick Help ==============================
                 +radio/<On|Off>  Turn your radio on or off.                  
       +radio <Letter>=<Message>  Sends a message over the channel.           
  +radio <Name1,NameN>=<Message>  Sends a message to the specified person/s.  
------------------------------------------------------------------------------
     +freq/set <Letter>=<Number>  Assigns a frequency to the letter.          
      +freq/name <Letter>=<Name>  Assigns a channel name to the letter.       
    +freq/title <Letter>=<Title>  Assigns a channel title.                    
    +freq/color <Letter>=<Color>  Assigns a color to the channel.             
                                  Ex. +freq/color a=FF88AA or 000000 or R     
            +freq/clear <Letter>  Clears all channel settings.                
              +freq/gag <Letter>  Gags the specific channel.                  
            +freq/total <Number>  Gives you more or less channels.            
       +freq/who <Letter|Number>  Displays who is on the channel.             
    +freq/swap <Letter>=<Letter>  Switches the two channels data in +radio.   
           +freq/recall <Letter>  50 lines of recall for the freq.            
  +freq/recall <Letter>=<Number>  X lines of recall for the freq.             
------------------------------------------------------------------------------
                    +radio/spoof  Toggles no_spoof on +radio.                 
                    +radio/color  Shifts from tag to full line color.         
                    +radio/reset  Clears all your frequencies.                
              +radio/<Jam|Unjam>  Jams or unjams your location.               
       +radio/intercept <On|Off>  Turns intercept on or off.                  
        +radio/intercept <Color>  Sets intercept messages color.              
           +radio/direct <Color>  Sets tightbeam messages color.              
                    +radio/clean  Clears unused frequencies from your         
                                  +radio.                                     
------------------------------- MOTD Commands --------------------------------
                    +freq/update  Copies the MoTD frequencies to your         
                                  +radio.                                     
                           +motd  Displays your factions MoTD and             
                                  frequencies.                                
                                                                              
    +freq/motd <Letter>=<Number>=<Title>  Sets a channel in +motd.            
  +freq/secure <Letter>=<Number>=<Title>  Sets a secure channel in +motd.     
      +freq/team <Team>=<Number>=<Title>  Sets a channel in +motd.            
   +freq/secteam <Team>=<Number>=<Title>  Sets a secure channel in +motd.     
==============================================================================


'''