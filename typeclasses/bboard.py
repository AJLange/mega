"""
Default Typeclass for Bulletin Boards, based partially on arx bboards.

Not sure if I will actually use this, but working with it for now. Bboard class is also defined
in the django models.

"""

from typeclasses.objects import Object
from world.boards.models import BoardPost, BulletinBoard
from server.utils import get_full_url


class BBoard(Object):
    """
    This is the base class for all Bulletin Boards. Inherit from this to create different
    types of communication bboards.
    """

    default_desc = "A bulletin board"

    def bb_post(
        self,
        poster_obj,
        msg,
        subject="No Subject",
        poster_name=None,
        event=None,
        announce=True,
    ):
        """
        Post the message to the board.
        """
        # noinspection PyArgumentList
        post = BoardPost(body_text=msg, db_title=subject)
        post.save()
        posted_by = "Unknown"
        if poster_obj:
            post.senders = poster_obj
            post.receivers = poster_obj
            posted_by = poster_obj
        if poster_name:
            post.db_sender_external = poster_name
            post.save()
            posted_by = poster_name
        self.tag_obj(post)
        if event:
            event.tag_obj(post)
        self.receiver_object_set.add(post)
        if self.max_posts and self.posts.count() > self.max_posts:
            posts = self.posts.exclude(db_tags__db_key="sticky_post")
            if "archive_posts" in self.tags.all():
                self.archive_post(posts.first())
            else:
                posts.first().delete()
            self.flush_unread_cache()
        if announce:
            post_num = self.posts.count()
            from django.urls import reverse

            post_url = get_full_url(
                reverse(
                    "msgs:post_view", kwargs={"board_id": self.id, "post_id": post.id}
                )
            )

            notify = "\n{{wNew post on {0} by {1}:{{n {2}".format(
                self.key, posted_by, subject
            )
            notify += "\nUse {w@bbread %s/%s {nor {w%s{n to read this message." % (
                self.key,
                post_num,
                post_url,
            )

            self.notify_subs(notify)
        self.update_cache_on_post(poster_obj)
        return post

    @property
    def max_posts(self):
        return self.db.max_posts or 100

    def notify_subs(self, notification):
        subs = [
            ob
            for ob in self.subscriber_list
            if self.access(ob, "read")
            and "no_post_notifications" not in ob.tags.all()
            and (not hasattr(ob, "is_guest") or not ob.is_guest())
        ]
        for sub in subs:
            sub.msg(notification)

    def has_subscriber(self, pobj):
        if pobj in self.subscriber_list:
            return True
        else:
            return False

    def get_unread_posts(self, pobj, old=False):
        """
        Get queryset of unread posts
        Args:
            pobj: AccountDB object
            old (bool or None): Whether we're using archive

        Returns:
            queryset of posts unread by pobj
        """
        if not old:
            return self.posts.all_unread_by(pobj)
        return self.archived_posts.all_unread_by(pobj)

    def num_of_unread_posts(self, pobj, old=False):
        if old:
            return self.get_unread_posts(pobj, old).count()
        if pobj in self.num_unread_cache:
            return self.num_unread_cache[pobj]
        num_unread = self.get_unread_posts(pobj, old).count()
        self.num_unread_cache[pobj] = num_unread
        return num_unread

    def get_post(self, pobj, postnum, old=False):
        # pobj is a player.
        postnum -= 1
        if old:
            posts = self.archived_posts
        else:
            posts = self.posts
        if (postnum < 0) or (postnum >= len(posts)):
            pobj.msg("Invalid message number specified.")
        else:
            return list(posts)[postnum]

    def get_latest_post(self):
        try:
            return self.posts.last()
        except BoardPost.DoesNotExist:
            return None

    def get_all_posts(self, old=False):
        if not old:
            return self.posts
        return self.archived_posts

    @property
    def subscriber_list(self):
        if self.db.subscriber_list is None:
            self.db.subscriber_list = []
        return self.db.subscriber_list

    def subscribe_bboard(self, joiner):
        """
        Run right before a bboard is joined. If this returns a false value,
        bboard joining is aborted.
        """
        if joiner not in self.subscriber_list:
            self.subscriber_list.append(joiner)
            return True
        else:
            return False

    def unsubscribe_bboard(self, leaver):
        """
        Run right before a user leaves a bboard. If this returns a false
        value, leaving the bboard will be aborted.
        """
        if leaver in self.subscriber_list:
            self.subscriber_list.remove(leaver)
            return True
        else:
            return False

    def delete_post(self, post):
        """
        Remove post if it's inside the bulletin board.
        """
        retval = False
        if post in self.posts:
            post.delete()
            retval = True
        if post in self.archived_posts:
            post.delete()
            retval = True
        self.flush_unread_cache()
        return retval

    @staticmethod
    def sticky_post(post):
        post.tags.add("sticky_post")
        return True

    @staticmethod
    def edit_post(pobj, post, msg):
        if post.tags.get(category="org_comment"):
            pobj.msg("The post has already had org responses.")
            return
        post.db_message = msg
        post.save()
        return True

    @property
    def posts(self):
        return BoardPost.objects.for_board(self).exclude(db_tags__db_key="archived")

    @property
    def archived_posts(self):
        return BoardPost.objects.for_board(self).filter(db_tags__db_key="archived")

    def read_post(self, caller, post, old=False):
        """
        Helper function to read a single post.
        """
        if old:
            posts = self.archived_posts
        else:
            posts = self.posts
        # format post
        sender = self.get_poster(post)
        message = "\n{w" + "-" * 60 + "{n\n"
        message += "{wBoard:{n %s, {wPost Number:{n %s\n" % (
            self.key,
            list(posts).index(post) + 1,
        )
        message += "{wPoster:{n %s\n" % sender
        message += "{wSubject:{n %s\n" % post.db_header
        message += "{wDate:{n %s\n" % post.db_date_created.strftime("%x %X")
        message += "{w" + "-" * 60 + "{n\n"
        message += post.db_message
        message += "\n{w" + "-" * 60 + "{n\n"
        caller.msg(message)
        if caller.is_guest():
            return
        # mark it read
        self.mark_read(caller, post)

    @staticmethod
    def archive_post(post):
        post.tags.add("archived")
        return True

    @staticmethod
    def mark_unarchived(post):
        post.tags.remove("archived")

    def mark_read_if_cache(self, caller):
        num_unread = self.num_unread_cache.get(caller, -1)
        if num_unread > 0:
            num_unread = num_unread - 1
        else:
            # We didn't have a cache and we'll already be marked read,
            # just take the value directly
            num_unread = self.get_unread_posts(caller, old=False).count()

        self.num_unread_cache[caller] = num_unread

    def mark_read(self, caller, post):
        if not post.db_receivers_accounts.filter(id=caller.id).exists():
            # Mark our post read
            post.db_receivers_accounts.add(caller)
            self.mark_read_if_cache(caller)

        if caller.db.bbaltread:
            try:
                for alt in (ob.player for ob in caller.roster.alts):
                    # Let's check this first, so we don't erroneously subtract
                    # from the cache a second time.
                    if not post.db_receivers_accounts.filter(id=alt.id).exists():
                        post.db_receivers_accounts.add(alt)
                        self.mark_read_if_cache(alt)

            except AttributeError:
                pass

    @property
    def num_unread_cache(self):
        if self.ndb.num_unread_cache is None:
            self.ndb.num_unread_cache = {}
        return self.ndb.num_unread_cache

    def update_cache_on_post(self, poster):
        for account in self.num_unread_cache:
            if account != poster:
                self.num_unread_cache[account] += 1

    def zero_unread_cache(self, poster):
        self.num_unread_cache[poster] = 0

    def flush_unread_cache(self):
        self.ndb.num_unread_cache = {}

    @staticmethod
    def get_poster(post):
        return post.poster_name

