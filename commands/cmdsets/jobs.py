"""
Job/Request module.

Jobs and apps will be in the database using a Request and Application model.

Player applications will still be by email until PC self-creation is working.
"""
from django.conf import settings

from evennia.utils.create import create_object
from typeclasses import prettytable

from evennia import default_cmds
from evennia import CmdSet
from commands import command
from evennia.commands.default.muxcommand import MuxCommand
from six import string_types
from server.utils import sub_old_ansi
from evennia.server.sessionhandler import SESSIONS
import time
import re
from evennia import ObjectDB, AccountDB
from evennia.utils import utils, create, evtable, make_iter, inherits_from, datetime_format
from evennia.comms.models import Msg
from evennia.commands.default.muxcommand import MuxCommand
from world.requests.models import Request,RequestResponse,File,Topic


def list_tickets(caller):
    """List tickets for the caller"""
    try:
        my_requests = Request.objects.filter(db_submitter=caller)
    except:
        caller.msg("No requests were found.")
        return
    msg = "\n|wMy Requests:|n\n\n"
    for request in my_requests:
        msg += "ID: %s  " % str(request.id)
        if request.db_is_open:
            msg += "Status: |gOpen|n \n"
        else:
            msg += "Status: |rClosed|n \n"
        msg += "Subject: %s\n" % request.db_title
        submit_time = request.db_date_created.strftime("%b %d, %Y")
        msg += "Sent on: %s\n" % submit_time
        if request.db_assigned_to:
            msg += "Assigned To: %s\n" % request.db_assigned_to
        else:
            msg += "Assigned To: Pending\n"
        msg += "\n"
    msg += "\nUse |w+request <#>|n to view an individual ticket. "
    caller.msg(msg)
    return

def list_open_tickets(caller):
    """List tickets for the caller"""
    try:
        my_requests = Request.objects.filter(db_submitter=caller)
    except:
        caller.msg("No requests were found.")
        return
    msg = "\n|wMy Requests:|n\n\n"
    for request in my_requests:
        if request.db_is_open:
            msg += "ID: %s  " % str(request.id)
            msg += "Subject: %s\n" % request.db_title
            submit_time = request.db_date_created.strftime("%b %d, %Y")
            msg += "Sent on: %s\n" % submit_time
            if request.db_assigned_to:
                msg += "Assigned To: %s\n" % request.db_assigned_to
            else:
                msg += "Assigned To: Pending\n"
            msg += "\n"
    msg += "\nUse |w+request <#>|n to view an individual ticket."
    caller.msg(msg)
    return

# TODO - this should list tickets assigned to me or unassigned?

def list_active_tickets(caller):
    """List tickets for staff side"""
    try:
        my_requests = Request.objects.filter(db_submitter=caller)
    except:
        caller.msg("No requests were found.")
        return
    msg = "\n|wMy Requests:|n\n\n"
    for request in my_requests:
        msg += "ID: %s  " % str(request.id)
        if request.db_is_open:
            msg += "Status: |gOpen|n \n"
        else:
            msg += "Status: |rClosed|n \n"
        msg += "Subject: %s\n" % request.db_title
        msg += "Request Type: %s" % request.get_type_display()
        msg += "\n"
    msg += "Use |w+request <#>|n to view an individual ticket. "
    caller.msg(msg)
    return

def get_ticket_from_args(caller, args):
    """Retrieve ticket or display valid choices if not found"""

    try:
        my_requests = Request.objects.filter(db_submitter=caller)
        ticket = my_requests.get(id=args)
        return ticket
    except (Request.DoesNotExist, ValueError):
        caller.msg("No request found by that number.")
        list_tickets(caller)
        return

def display_ticket(caller, ticket):
    msg = "\n|wRequest " + str(ticket.id) + "|n \n"
    if ticket.db_is_open:
        msg += "Status: |gOpen|n"
    else:
        msg += "Status: |rClosed|n"
    submit_time = ticket.db_date_created.strftime("%b %d %Y")
    msg += "\nSent on: %s\n" % submit_time
    msg += "\nSubject: " + ticket.db_title + "\n\n" + ticket.db_message_body + "\n"

    caller.msg(msg)
    return

def find_file(caller, value):
    #placeholder to see if a file is found matching check
    try:
        int(value)
    except ValueError:
        caller.msg("Please use a number for a file.")
        return 0
    my_files = caller.db.files
    for file in my_files:
        if file.id == value:
            return file
    caller.msg("404: file not found.")
    return 0

def search_all_files(caller, value):
    try:
        int(value)
    except ValueError:
        caller.msg("Please use a number for a file.")
        return 0
    my_files = File.objects.all()
    for file in my_files:
        if file.id == value:
            return file
    caller.msg("404: file not found.")
    return 0

class CmdRequest(MuxCommand):
    """
    +request - Make a request for GM help

    Usage:
       +request
       +request <#>
       +request/old

       +request <title>=<description>
       +request/bug <title>=<description>
       +request/char <title>=<description>
       +request/news <title>=<description>
    
    This command requests <title> and <description> from staff. The request is    
    added to the jobs list and will be tended to as soon as possible. There is a  
    standard three to four day turnaround time on +requests.                      

    +request is a method of getting information about any subject, IC or OOC, from
    the administration. It is used to get details about the world, request        
    background plot information, investigate ongoing TPs, and to contact the admin
    for various OOC purposes.

    Typing just +request with no arguments gives you back your list of active
    +requests. This lists your active submissions to +request, showing title, admin 
    assigned if any, and the date of submission.
    
    +request <#> to view the text of that request and any response chain.

    By default, +request only lists active requests which have not been answered,
    but +request/old will show you requests staff has archived (but not deleted).
    Keep in mind that some requests such as bug reports may be deleted by staff
    after they are handled.

    If an old request is answered with a file, the file should be mentioned
    in your request response. See help +files.    
    """

    key = "request"
    aliases = ["requests", "+request","+requests"]
    help_category = "Requests"
    locks = "perm(Player))"

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args
        switches = self.switches

        if not args:
            if "old" in switches:
                list_tickets(caller)
                return
            else:
                list_open_tickets(caller)
                return
        

        if self.lhs.isdigit():
            ticket = get_ticket_from_args(caller, self.lhs)
            if not ticket:
                return

            display_ticket(caller, ticket)
            return
        elif not self.lhs.isdigit:
            caller.msg("Please enter a number for the request you want to view.")
            return

        category = 1

        if switches:
            if "bug" in switches:
                category = 2
            if "char" in switches:
                category = 3
            if "news" in switches:
                category = 4
        
        title = self.lhs
        message = sub_old_ansi(self.rhs)
        if not message:
            caller.msg("Syntax error - no message. +request <title>=<message>.")
            return

        new_ticket = Request.objects.create(db_title=title, db_submitter=caller,db_message_body=message,type=category)
        if new_ticket:
            caller.msg(
                f"Thank you for submitting a request to the GM staff. Your ticket (#{new_ticket.id}) "
                "has been added to the queue."
            )
        else:
            caller.msg(
                "Request submission has failed for unknown reason. Please inform the administrators."
            )


class CmdMyPlayerJobs(MuxCommand):
    """
    Command for players to check their old requests.

    Usage:
       +myjobs
       +myjob <#>
       +myjobs/old
    
    +myjobs lists your active submissions to +request, showing title, admin 
    assigned if any, and the date of submission.

    +myjob <#> will show you the text of the job submitted by you, and any 
    response chain there might be.

    By default, +myjobs only lists active requests which have not been answered,
    but +myjobs/old will show you all old +requests in a list for you to
    review.

    This command is only to review and read. To submit, see +request.
    
    If an old request is answered with a file, that file name will be 
    in your request response. See help +files.

    """

    key = "myjobs"
    aliases = ["+myjobs", "myjob", "+myjob"]
    help_category = "Requests"
    locks = "perm(Player))"

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args
        switches = self.switches

        if not args:
            self.list_tickets()
            return


class CmdCheckJobs(MuxCommand):
    """
    Command for admin to check request queue.

    Usage:
       +jobs
       +job <#>

       +job/assign <#>=<person>
       +job/category <#>=<category>
       +job/file <#>=<file>
       +job/respond <#>=<description>
       +job/add <#>=<description>
       +job/close <#>
       +job/kill <#>

       +jobs/old 

    This command is for staff to answer requests.

    +jobs shows all active (not closed) +requests.
    +job <#> shows the text of one, with history.

    +job/assign to flag a job for a certain staffer to answer.
    +job/category to put a job in a particular category.
    +job/file attaches a file to a job.
    +job/respond creates a one-off response and sends it out.
    Be careful not to create one-off off responses that should be files.

    +job/add will allow you to tag in other people to a job.

    +job/close to archive a job, removing it from active job list.
    This also puts it in an archive for the player (they can read with
    +myjobs/old.)

    +job/kill deletes a job entirely. This is for jobs that are resolved
    and do not need to be archived. (They can still be un-deleted from the
    database if you kill a job in error.)

    If you want to read all archived jobs, use +jobs/old. This is probably
    very spammy.

    """

    key = "job"
    aliases = ["jobs","job", "+job"]
    help_category = "Requests"
    locks = "perm(Builder))"
    
    def close_ticket(self, number, reason):
        caller = self.caller

        ticket = get_ticket_from_args(number)
        if not ticket:
            return

        if ticket:            
            caller.msg(f"You have successfully closed ticket #{ticket.id}.")
        else:
            caller.msg(f"Failed to close ticket #{ticket.id}.")

        return
    
    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args
        switches = self.switches

        if not args:
            list_active_tickets(caller)
            return


class CmdCheckFiles(MuxCommand):
    """
    Command to read files sent to you about story.

    Usage:
       +files
       +file <#>

       +file/send <#>=<person>
       +file/share <#>=<group>

          
    This command is to share files among players.

    It's just outlined.
    +file/send to send along a file to another player.
    +file/share to share a file to an entire group.

    Files contain lore which is ICly known. It is usually the subject of a research
    +request.

    """

    key = "file"
    aliases = ["files","+file","+files"]
    help_category = "Requests"
    locks = "perm(Player))"



    def func(self):
        """Implement the command"""
        caller = self.caller
        switches = self.switches
        errmsg= "Syntax error. Check +help +file."

        if "send" in switches:
            num = self.lhs
            person = self.rhs
            if not person:
                caller.msg(errmsg)
                return
            file = find_file(num)
            if not file:
                caller.msg(f"Didn't see a file {num} in your possession.")
                return
            # TODO - do the sending
            # TODO - accept a comma seperated list
            caller.msg(f"Sent file {num} to {person}.")
            return
        
        if "share" in switches:
            num = self.lhs
            group = self.rhs
            if not group:
                caller.msg(errmsg)
                return
            file = find_file(num)
            if not file:
                caller.msg(f"Didn't see a file {num} in your possession.")
                return
            # TODO - do the posting
            caller.msg(f"Shared file {num} to {group}.")
            return
        
        if not switches:
            if not self.args:
                caller.msg("List all files known:")
                # TODO - actually get them
            else:
                file = self.args
                try:
                    file_num = int(file)
                except ValueError:
                    caller.msg(errmsg)
                    return
                file = find_file(file_num)
                if not file:
                    caller.msg(f"No file {file_num} found in your possession.")
                    return
                caller.msg("This would be the text of the file:")
                return

        else:
            caller.msg(errmsg)
            return


class CmdCreateFile(MuxCommand):
    """
    Command for staff to create files. 

    Usage:
       +writefile <title>=<text>
       +writefile/keyword <#>=<keyword>
       +writefile/topic <#>=<topic>
       +writefile/archive <#>

    This command is to compose files. +writefile creates the basic file
    and can take all the text of the file.

    +writefile/keyword adds the supplied keyword to the file.
    +writefile/topic files the file under the specified topic.

    +writefile/archive <#> will mark a file as obsolete. This is to be used
    if a file is no longer useful.

    Files can be edited by database admin, but a command to edit files will
    be written in the future if needed.

    To send a file to a player, use +file/send <#>=<player> once the file 
    is complete.

    """

    key = "writefile"
    aliases = ["+writefile"]
    help_category = "Requests"
    locks = "perm(Builder))"

    # write these searches
    def find_keyword(self, word):
        keyword = word
        return keyword

    def find_topic(self, word):
        topic = word
        return topic

    def func(self):
        """Implement the command"""
        caller = self.caller
        switches = self.switches
        errmsg= "Syntax failure. Check +help +writefile."

        if "topic" in switches:
            num = self.lhs
            topic = self.rhs

            if not topic:
                caller.msg(errmsg)
                return
            
            #find this file
            file = search_all_files(num)
            if not file:
                caller.msg(f"No file {num} found.")
                return
            # seek matching topic
            file_topic = self.find_topic(topic)
            # if no matching topic, create it, warn caller
            if not file_topic:
                caller.msg(f"No topic was found, so created new topic: {topic}")

            # file the file in the topic.
            caller.msg(f"Added file {num} to {topic}.")

        if "keyword" in switches:
            num = self.lhs
            word = self.rhs
            if not word:
                caller.msg(errmsg)
                return
            
            # TODO - make sure word is a string, and lowercase it

            #find this file
            file = search_all_files(num)
            if not file:
                caller.msg(f"No file {num} found.")
                return
            #seek matching keyword
            keyword = self.find_keyword(word)
            #if keyword not found, create new keyword, warn caller
            if not keyword:
                caller.msg(f"No keyword was found, so created new keyword: {word}")

            # file the file in the topic.
            caller.msg(f"Added keyword {word} to file {num}.")

        if "archive" in switches:
            num = self.args
            if not num:
                caller.msg(errmsg)
                return
            #do archival
            file = search_all_files(num)
            if not file:
                caller.msg(f"No file {num} found.")
                return
            if not file.up_to_date:
                caller.msg("That file is already archived.")
                return
            else:
                file.up_to_date = False
                caller.msg(f"Archived file {num}, marking it obsolete.")

        if not switches:
            title = self.lhs
            message = self.rhs
            
            if not message:
                caller.msg(errmsg)
                return
            
            message = sub_old_ansi(message)
            new_file = File.objects.create(db_title=title, db_author=caller, db_text=message)
            if new_file:
                caller.msg(f"You created the file number (#{new_file.id}) Use +file/send to share it to a player.")
                return
            else:
                caller.msg("File creation failed for unknown reason. Ask your codestaff what broke!")
                return
            
        else:
            caller.msg(errmsg)
            return