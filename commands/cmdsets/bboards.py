from evennia.utils import create
from evennia.utils.create import create_object
from typeclasses import prettytable
from evennia.utils.evtable import EvTable
from evennia import default_cmds
from server.utils import sub_old_ansi
from world.boards.models import BulletinBoard, BoardPost
from commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand


def get_boards():
    """
    returns list of bulletin boards
    """
    bb_list = list(BulletinBoard.objects.all())

    return bb_list

def list_bboards(caller):
    """
    Helper function for listing all boards a player is subscribed
    to in some pretty format.
    """
    bb_list = get_boards()
    if not bb_list:
        caller.msg("No boards were found.")
        return
    # later set this on the account level, which involves change of model
    my_subs = []
    for bb in bb_list:
        if caller in bb.has_subscriber.all():
            my_subs.append(bb)

    # just display the subscribed bboards with no extra info
    
    bbtable = EvTable(
        "bb #", "Name", "New Posts", "Subscribed"
        )
    for bboard in bb_list:
        bb_number = bb_list.index(bboard)
        bb_name = bboard.db_name

        unread_num = get_num_unread(caller, bboard)
        subbed = bboard in my_subs
        
        bbtable.add_row(bb_number, bb_name, unread_num, subbed)
    caller.msg("\n" + "=" * 70 + "\n%s" % bbtable)

def check_if_subbed(caller, board_to_check):
    board_subs = board_to_check.has_subscriber.all()
    if not caller in board_subs:
        caller.msg("You are not yet a subscriber to {0}.".format(board_to_check.db_name))
        caller.msg("Use bbsub to subscribe to it.")
        return False
    else:
        return True

def access_bboard(caller, args, request="read"):
    """
    Helper function for searching for a single bboard with
    some error handling.
    """
    bboards = get_boards()
    if not bboards:
        return
    if args.isdigit():
        bb_num = int(args)
        if (bb_num < 0) or (bb_num >= len(bboards)):
            caller.msg("Invalid board number.")
            return
        board = bboards[bb_num]

    else:
        board_ids = [ob.id for ob in bboards]
        try:
            board = BulletinBoard.objects.get(db_key__icontains=args, id__in=board_ids)
        except BulletinBoard.DoesNotExist:
            caller.msg("Could not find a unique board by name %s." % args)
            return
        except BulletinBoard.MultipleObjectsReturned:
            boards = BulletinBoard.objects.filter(db_key__icontains=args, id__in=board_ids)
            caller.msg(
                "Too many boards returned, please pick one: %s"
                % ", ".join(str(ob) for ob in boards)
            )
            return
    if not check_access(caller, board):
        caller.msg("You do not have the permissions to view that board.")
        return
    # passed all checks, so return board
    return board

def get_all_posts(board):
    posts = []
    try:
        posts = BoardPost.objects.filter(db_board = board)
    except LookupError:
        return 
    return posts

def list_messages(caller, board):
    """
    Helper function for printing all the posts on board
    to caller.
    """
    if not board:
        caller.msg("No bulletin board found.")
        return
    caller.msg("" + "=" * 60 + "\n")
    title = "**** %s ****" % board.db_name.capitalize()
    title = "{:^60}".format(title)
    caller.msg(title)
    posts = get_all_posts(board)
    if not posts:
        caller.msg = "No posts found yet on this board."
        return
    msgnum = 0
    msgtable = EvTable(
        "bb/msg", "Subject", "PostDate", "Posted By"
    )

    # to do - posts track if they are read-by characters.
    # not working for now.
    
    unread_posts = get_unread_posts(caller)

    for post in posts:
        unread = post in unread_posts
        msgnum += 1
        if str(board).isdigit():
            bbmsgnum = str(board) + "/" + str(msgnum)
        else:
            bbmsgnum = board.db_name.capitalize() + "/" + str(msgnum)
        # if unread message, make the message white-bold
        if unread:
            bbmsgnum = "" + "{0}".format(bbmsgnum)
        subject = post.db_title[:35]
        date = post.db_date_created.strftime("%x")
        poster = post.posted_by
        # turn off white-bold color if unread message
        if unread:
            poster = "{0}".format(poster) + ""
        msgtable.add_row(bbmsgnum, subject, date, poster)
    caller.msg(str(msgtable))
    pass

def get_num_unread(caller, board):
    
    post_list = list(BoardPost.objects.all())
    unread = []
    for post in post_list:
        if board == post.db_board:
            if caller in post.read_by.all():
                continue
            else:
                unread.append(post)
    unread_int = len(unread)
    return unread_int

def get_unread_posts(caller):
    bb_list = get_boards()
    if not bb_list:
        return
    my_subs = []
    for bb in bb_list:
        if caller in bb.has_subscriber.all():
            my_subs.append(bb)
    msg = "New @bb posts in: "
    post_list = list(BoardPost.objects.all())
    unread = []
    for post in post_list:
        if caller in post.read_by.all():
            continue
        else:
            unread.append(post)
    if len(unread) == 0:
        caller.msg("There are no unread posts on your subscribed bboards.")
        return 0
    return unread
    for bb in my_subs:
        post = bb.get_latest_post()
        if not post:
            continue
        if not post.check_read(caller):
            unread.append(bb)
    if unread:
        msg += ", ".join(bb.key.capitalize() for bb in unread)
        caller.msg(msg)
    else:
        caller.msg("There are no unread posts on your subscribed bboards.")

def check_access(caller, board):
    # boards = get_boards()
    player_groups = caller.db.pcgroups
    board_groups = board.db_groups.all()
    if not board_groups:
        # assume all access
        return True
        #otherwise:
    for group in board_groups:
        if group in player_groups:
            return True
        else:
            return False

def read_post(board, post_num):
    post = "**** %s ****" % board.db_name.capitalize()
    post += "Subject: " + post_num.posted_by + "\n"
    post += "Author: " + post_num.db_title + "\n\n"
    post += post_num.body_text
    return post

'''
to add- board timeout function for server using the board timeout value

'''

class CmdGetUnreadPosts(MuxCommand):
    """
    +bbunread - get unread posts
    """

    key = "bbunread"
    aliases = ["@bbunread", "+bbunread"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        caller = self.caller
        get_unread_posts(caller)

class CmdBBNew(MuxCommand):

    """
    bbnext to read an unread post from boards you are subscribed to

    Usage:
        +bbnext - retrieve a single post
        +bbnext <number of posts>[=<board num>] - retrieve posts
        +bbnext/all[=<board num>] - retrieve all posts

    This command will retrieve unread messages. If an argument is passed,
    it will retrieve up to the number of messages specified.

    You can use bbnext/all (or bbcatchup) to instantly see all unread posts.

    """

    key = "bbnext"
    aliases = ["+bbnext", "@bbnext", "bbnew", "+bbnew", "+bbcatchup", "bbcatchup"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.lhs
        bb_list = get_boards()
        my_subs = []

        if not bb_list:
            return
        if not self.rhs:
            for bb in bb_list:
                if caller in bb.has_subscriber.all():
                    my_subs.append(bb)
        else:
            sub = access_bboard(caller, self.rhs)
            if sub:
                my_subs.append(sub)
        if not my_subs:
            caller.msg("Currently not subscribed to any boards.")
            return
        if not args:
            num_posts = 1
        elif "all" in args:
            num_posts = 500
        else:
            try:
                num_posts = int(args)
            except ValueError:
                caller.msg("Argument must either be 'all' or a number.")
                return
        # found_posts = 0
        # caller.msg("Unread posts:\n{}".format("-" * 60))
        # noread = "markread" in self.switches
        unread_count = 0
        for bb in my_subs:
            posts = bb.get_unread_posts(caller.account)
            if not posts:
                continue
            unread_count += 1
            # caller.msg("Board %s:" % bb.key)
            # posts_on_board = 0
            for post in posts:
                bb.read_post(caller, post)
                # if noread:
                #     bb.mark_read(caller, post)
                # else:
                #     bb.read_post(caller, post)
                # found_posts += 1
                # posts_on_board += 1
                # if found_posts >= num_posts:
                #     return
            # if noread:
            #     self.msg("You have marked %s posts as read." % posts_on_board)
        # if not found_posts:
        #     self.msg(
        #         "No new posts found on boards: %s."
        #         % ", ".join(str(sub) for sub in my_subs)
        #     )
        if unread_count != 0:
            caller.msg("Marked posts as read.")
        else:
            caller.msg("There are no unread posts on your subscribed bboards.")

class CmdBBRead(MuxCommand):

    """
    bbread to read posts on the bboards you are subscribed to.

    Usage:
        +bbread
        +bbread <Board Number>
        +bbread <Board Number>/<Message Number>

    The first command in the list returns a list of all the boards you are
    currently subscribed to. (You can also use +bblist for this.)

    The second command returns a list of all the posts made to the given  
    board.

    The third command returns a specific post on the given board.

    See also bbpost, bbedit, bbdel commands.

    """

    key = "bbread"
    aliases = ["+bbread", "@bbread", "bread", "+bread", "+bblist", "bblist"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        caller = self.caller
        args = self.args

        if self.cmdstring == "bread" or self.cmdstring == "+bread":
            caller.msg("I assumed you meant bbread, but just in case, here's bread: https://www.youtube.com/watch?v=bHK0uFb6Vzw ")

        if not args:
            list_bboards(caller)
            return
        
        if self.cmdstring == "bblist" or self.cmdstring == "+bblist":
            #assuming I want the old bblist command
            list_bboards(caller)
            return
        
        # do the reading not listing 
        arglist = args.split("/")
        board_num = arglist[0]
        board_to_check = access_bboard(caller, board_num)
        if not board_to_check:
            return
        subbed = check_if_subbed(caller, board_to_check)
        access = check_access(caller, board_to_check) 
        if not subbed:
            return
        if not access:
            caller.msg("You don't the permissions necessary to read that board.")
            return
        
        if len(arglist) < 2:
            list_messages(caller, board_to_check)
            return
        
        else:
            #Build and read a post
            post_num = arglist[1]
            post = read_post(board_num, post_num)
            caller.msg(post)



class CmdBBPost(MuxCommand):
    """
    Post to boards that you are subscribed to.

    Usage:
       +bbpost <Board Number>/<Subject>=<Message>

    Use this syntax to post a new message to a bboard.

    Example:
       +bbpost 1/Greetings=This is my first post!
       bbpost 2/It's OK=The plus sign is optional.%R%RMUSH format works!

    Bulletin Boards are intended to be discussion groups divided
    by topic for news announcements.

    Most boards are considered OOC communication.

    Group-related boards are considered IC communication and can be used
    to share information between characters in those groups. This is a 
    good way for groups to be connected about RP they may have missed while
    offline. Please keep in mind that even if you can see a board OOCly,
    you can only ICly use information that you know ICly, such as being 
    a member of said group. Use boards responsibily!

    To subscribe to a board, use 'bbsub'. To read the newest post on
    a board, use bbnew.
    
    """

    key = "bbpost"
    aliases = ["+bbpost"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned), perm(Player)"
    # guests can read but only players should post.

    def func(self):
        """Implement the command"""
        caller = self.caller
        args = self.args
        
        if not args:
            caller.msg("Syntax: +bbpost <Board Number>/<Subject>=<Message>")
            return
        
        if not self.rhs:
                caller.msg("Usage: +bbpost <Board Number>/<Subject>=<Message>")
                return
        lhs = self.lhs
        arglist = lhs.split("/")
        if len(arglist) < 2:
            subject = "No Subject"
        else:
            subject = arglist[1].lstrip()
            if subject == "":
                subject = "No Subject"
            board = access_bboard(caller, arglist[0], "write")
            if not board:
                return
            message = self.rhs
            message = sub_old_ansi(message)
            # board.bb_post(caller, message, subject)
            bbpost = BoardPost.objects.create(db_title=subject, db_board=board, posted_by=caller,body_text=message)
            if not bbpost:
                caller.msg("Sorry, something went wrong. Usage: +bbpost <Board Number>/<Subject>=<Message>")
            else:
                caller.msg(f"Created post {subject} to board {board}.")
        return

class CmdBBEdit(MuxCommand):
    """
    bbedit to edit a segment of a post that you have already posted.

    Usage:
       +bbedit <Board Number>/<Message Number>=<Old Text>/<New Text>

    This command will search out for something within a post you made, and
    replace it with the new text. 

    Example:
      I'm a hungry boy who eats chips potato.
      +bbedit 2/13=eats chips potato/eats potato chips
      I'm a hungry boy who eats potato chips.

    """

    key = "bbedit"
    aliases = ["+bbedit"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        """Implement the command"""

        caller = self.caller
        lhs = self.lhs
        arglist = lhs.split("/")
        if len(arglist) < 2 or not self.rhs:
            self.msg("Usage: bbedit <Board Number>/<Message Number>=<Old Text>/<New Text>")
            return
        try:
            post_num = int(arglist[1])
        except ValueError:
            self.msg("Invalid post number.")
            return
        board = access_bboard(caller, arglist[0], "write")
        if not board:
            return
        post = board.get_post(caller, post_num)
        if not post:
            return
        if not caller.account.check_permstring("Admins"):
            if (caller not in post.db_sender_accounts.all() and not board.access(
                    caller, "edit"
                )) or caller.key.upper() != post.poster_name.upper():
                    caller.msg("You cannot edit someone else's post, only your own.")
                    return
            if board.edit_post(self.caller, post, sub_old_ansi(self.rhs)):
                self.msg("Post edited.")

class CmdBBDel(MuxCommand):

    """
    bbdel - delete my post.

    Usage:
       bbdel <board>/<post>

    Removes a post that you have made from a bboard.

    """
    key = "bbdel"
    aliases = ["+bbdel", "bbremove", "+bbremove", "bbdelete", "+bbdelete"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        """Implement the command"""

        caller = self.caller
        args = self.lhs
        switchname = "del"
        verb = "delete"
        method = "delete_post"
        switches = self.switches
        board = args
        if board.tags.get("only_staff_delete") and not caller.check_permstring(
                    "builders"
                ):
                    self.msg("Only builders may delete from that board.")
                    return
        else:
            switchname = "archive"
            verb = "archive"
            method = "archive_post"
        if len(args) < 2:
            caller.msg("Usage: @bb/%s <board #>/<post #>" % switchname)
            return
        try:
            post_num = int(args[1])
        except ValueError:
            caller.msg("Invalid post number.")
            return
        post = board.get_post(caller, post_num)
        if not post:
            return
        if not caller.account.check_permstring("Admins"):
            if (caller not in post.db_sender_accounts.all() and not board.access(
                    caller, "edit"
                )) or caller.key.upper() != post.poster_name.upper():
                    caller.msg("You cannot %s someone else's post, only your own." % verb)
                    return
            if getattr(board, method)(post):
                caller.msg("Post %sd" % verb)

            else:
                caller.msg("Post %s failed for unknown reason." % verb)
            return


class CmdBBStick(MuxCommand):
    """
    bbstick - Make a post a sticky post

    Usage:
       bbstick <board #>/<post #>

    This staff only command will over-ride the timeout on a board,
    keeping the indicated post alive on the board until it is manually
    deleted.

    """

    key = "bbstick"
    aliases = ["@bbstick", "+bbstick"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned), perm(Builder)"

    def func(self):
        """Implement the command"""

        caller = self.caller
        args = self.args
        errmsg = "Syntax: bbstick <board #>/<post #>"

        if not args:
            caller.msg("Stick which post?")
            return
        
        arglist = args.split("/")
        if len(arglist) < 2:
            caller.msg(errmsg)
            return
        
        board = access_bboard(arglist[0])
        post_num = arglist[1]
        #command parsed, go ahead and do the thing

class CmdBBSub(MuxCommand):
    """
    bbsub - subscribe to a bulletin board

    Usage:
       bbsub <board #>
       bbsub/add <board #>=<player>

    Subscribes to a board of the given number.
    """

    key = "bbsub"
    aliases = ["@bbsub", "+bbsub"]
    help_category = "Comms"
    locks = "cmd:not pperm(bboard_banned)"

    def func(self):
        """Implement the command"""

        caller = self.caller
        args = self.lhs

        if not args:
            self.msg("Usage: bbsub <board #>.")
            return

        bboard = access_bboard(caller, args)
        if not bboard:
            return

        # check permissions
        if not check_access(caller, bboard):
            self.msg("%s: You are not allowed to view this bboard." % bboard.key)
            return
        if "add" in self.switches:
            if not caller.check_permstring("builders"):
                caller.msg("You must be a builder or higher to use that switch.")
                return
            targ = caller.search(self.rhs)
        else:
            targ = caller
        if not targ:
            return
        for sub in bboard.has_subscriber.all():
            if sub == caller:
                caller.msg("%s is already subscribed to that board." % targ)
                return
        #wasn't found on list so add to list
        bboard.has_subscriber.add(caller)
        caller.msg("Successfully subscribed %s to %s" % (targ, bboard.db_name))


class CmdBBUnsub(default_cmds.MuxCommand):
    """
    bbunsub - unsubscribe from a bulletin board

    Usage:
       bbunsub <board #>

    Removes a bulletin board from your list of subscriptions.
    """

    key = "bbunsub"
    aliases = ["@bbunsub, +bbunsub"]
    help_category = "Comms"
    locks = "cmd:not perm(bboard_banned)"

    def func(self):
        """Implementing the command."""

        caller = self.caller
        args = self.args
        found = False
        if not args:
            self.msg("Usage: bbunsub <board #>.")
            return
        bboard = access_bboard(caller, args)
        if not bboard:
            return
        for sub in bboard.has_subscriber.all():
            if sub == caller:
                found = True
                bboard.has_subscriber.remove(caller)
                caller.msg("Unsubscribed from %s" % bboard.db_name)
                return
        if not found:
            caller.msg(f"You were not subscribed to board {args}.")


class CmdBBCreate(MuxCommand):
    """
 
    Usage:
       bbcreate <boardname>

    Creates a new bboard.
    Use the command bbperms to add groups to board permissions.

    """

    key = "bbcreate"
    aliases = ["+bbcreate", "@bbcreate"]
    locks = "cmd:perm(bbcreate) or perm(Wizards)"
    help_category = "Comms"

    def func(self):
        """Implement the command"""

        caller = self.caller

        if not self.args:
            self.msg("Usage: bbcreate <boardname>")
            return

        lhs = self.lhs
        bboardname = lhs
        # Create and set the bboard up
        lockstring = "edit:all();write:all();read:all();control:id(%s)" % caller.id

        new_board = BulletinBoard.objects.create(db_name =bboardname)

        self.msg("Created bboard %s." % new_board.db_name)
        #new_board.subscribe_bboard(caller)
        #new_board.save()


class CmdBBPerms(MuxCommand):
    """
 
    Usage:
       bbperms <boardname>=<group>

    Add a group to the permissions for a bboard.
    This accepts player groups and permission groups (aka, staff).

    Does not work yet!

    """

    key = "bbperms"
    aliases = ["+bbperms", "@bbperms"]
    locks = "cmd:perm(bbcreate) or perm(Wizards)"
    help_category = "Comms"

    def func(self):
        """Implement the command"""

        caller = self.caller

        if not self.args:
            self.msg("Usage: bbperms <boardname>=<group>")
            return

        lhs = self.lhs
        bboardname = lhs
        # Create and set the bboard up
        lockstring = "edit:all();write:all();read:all();control:id(%s)" % caller.id

        new_board = BulletinBoard.objects.create(db_name =bboardname, db_groups=None)

        self.msg("Created bboard %s." % new_board.db_name)
        #new_board.subscribe_bboard(caller)
        #new_board.save()