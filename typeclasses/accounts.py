import re
import time
from django.conf import settings
from evennia.accounts.models import AccountDB
from evennia.server.throttle import Throttle
from evennia import DefaultAccount
from evennia.utils import class_from_module, create, logger
# Create throttles for too many account-creations and login attempts
CREATION_THROTTLE = Throttle(
    limit=settings.CREATION_THROTTLE_LIMIT, timeout=settings.CREATION_THROTTLE_TIMEOUT
)
LOGIN_THROTTLE = Throttle(
    limit=settings.LOGIN_THROTTLE_LIMIT, timeout=settings.LOGIN_THROTTLE_TIMEOUT
)

"""
Account

The Account represents the game "account" and each login has only one
Account object. An Account is what chats on default channels but has no
other in-game-world existence. Rather the Account puppets Objects (such
as Characters) in order to actually participate in the game world.


Guest

Guest accounts are simple low-level accounts that are created/deleted
on the fly and allows users to test the game without the commitment
of a full registration. Guest accounts are deactivated by default; to
activate them, add the following line to your settings file:

    GUEST_ENABLED = True

You will also need to modify the connection screen to reflect the
possibility to connect with a guest account. The setting file accepts
several more options for customizing the Guest account system.

"""




class Account(DefaultAccount):
    """
    This class describes the actual OOC account (i.e. the user connecting
    to the MUD). It does NOT have visual appearance in the game world (that
    is handled by the character which is connected to this). Comm channels
    are attended/joined using this object.

    It can be useful e.g. for storing configuration options for your game, but
    should generally not hold any character-related info (that's best handled
    on the character level).

    Can be set using BASE_ACCOUNT_TYPECLASS.


    * available properties

     key (string) - name of account
     name (string)- wrapper for user.username
     aliases (list of strings) - aliases to the object. Will be saved to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     user (User, read-only) - django User authorization object
     obj (Object) - game object controlled by account. 'character' can also be used.
     sessions (list of Sessions) - sessions connected to this account
     is_superuser (bool, read-only) - if the connected user is a superuser

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create a database entry when storing data
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().

    * Helper methods

     msg(text=None, **kwargs)
     execute_cmd(raw_string, session=None)
     search(ostring, global_search=False, attribute_name=None, use_nicks=False, location=None, ignore_errors=False, account=False)
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hook methods (when re-implementation, remember methods need to have self as first arg)

     basetype_setup()
     at_account_creation()

     - note that the following hooks are also found on Objects and are
       usually handled on the character level:

     at_init()
     at_cmdset_get(**kwargs)
     at_first_login()
     at_post_login(session=None)
     at_disconnect()
     at_message_receive()
     at_message_send()
     at_server_reload()
     at_server_shutdown()

    """

    pass


class MegaGuest(DefaultAccount):
    """
    This class is used for guest logins. Unlike Accounts, Guests and
    their characters are deleted after disconnection.
    """

    @classmethod
    def create(cls, **kwargs):
        """
        Forwards request to cls.authenticate(); returns a DefaultGuest object
        if one is available for use.
        """
        return cls.authenticate(**kwargs)

    @classmethod
    def authenticate(cls, **kwargs):
        """
        Gets or creates a Guest account object.

        Keyword Args:
            ip (str, optional): IP address of requestor; used for ban checking,
                throttling and logging

        Returns:
            account (Object): Guest account object, if available
            errors (list): List of error messages accrued during this request.

        """
        errors = []
        account = None
        username = None
        ip = kwargs.get("ip", "").strip()

        # check if guests are enabled.
        if not settings.GUEST_ENABLED:
            errors.append(("Guest accounts are not enabled on this server."))
            return None, errors

        try:
            # Find an available guest name.
            for name in settings.GUEST_LIST:
                if not AccountDB.objects.filter(username__iexact=name).exists():
                    username = name
                    break
            if not username:
                errors.append(("All guest accounts are in use. Please try again later."))
                if ip:
                    LOGIN_THROTTLE.update(ip, "Too many requests for Guest access.")
                return None, errors
            else:
                # build a new account with the found guest username
                password = "genericguestpassword1"
                home = settings.GUEST_HOME
                permissions = settings.PERMISSION_GUEST_DEFAULT
                typeclass = settings.BASE_GUEST_TYPECLASS

                # Call parent class creator
                account, errs = super(MegaGuest, cls).create(
                    guest=True,
                    username=username,
                    password=password,
                    permissions=permissions,
                    typeclass=typeclass,
                    home=home,
                    ip=ip,
                )
                errors.extend(errs)

                if not account.characters:
                    # this can happen for multisession_mode > 1. For guests we
                    # always auto-create a character, regardless of multi-session-mode.
                    character, errs = account.create_character()

                if errs:
                    errors.extend(errs)

                return account, errors

        except Exception as e:
            # We are in the middle between logged in and -not, so we have
            # to handle tracebacks ourselves at this point. If we don't,
            # we won't see any errors at all.
            #errors.append(_("An error occurred. Please e-mail an admin if the problem persists."))
            #logger.log_trace()
            return None, errors

        return account, errors

    def at_post_login(self, session=None, **kwargs):
        """
        In theory, guests only have one character regardless of which
        MULTISESSION_MODE we're in. They don't get a choice.

        Args:
            session (Session, optional): Session connecting.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        """
        self._send_to_connect_channel(("|G{key} connected|n").format(key=self.key))
        self.puppet_object(session, self.db._last_puppet)

    def at_server_shutdown(self):
        """
        We repeat the functionality of `at_disconnect()` here just to
        be on the safe side.
        """
        super().at_server_shutdown()
        characters = self.db._playable_characters
        for character in characters:
            if character:
                character.delete()

    def at_post_disconnect(self, **kwargs):
        """
        Once having disconnected, destroy the guest's characters and

        Args:
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        """
        super().at_post_disconnect()
        characters = self.db._playable_characters
        for character in characters:
            if character:
                character.delete()
        self.delete()


class Guest(MegaGuest):
    """
    This class is used for guest logins. Unlike Accounts, Guests and their
    characters are deleted after disconnection.
    """

    def at_first_login(self):
        #self.remove(default_cmdsets.CharacterCmdSet())

        pass
