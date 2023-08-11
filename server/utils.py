"""
General helper functions that don't fit neatly under any given category.

These helper functions are modified from the Arx helper functions.

"""
import re
from datetime import datetime

from django.conf import settings


def setup_log(logfile):
    """Sets up a log file"""
    import logging

    file_handle = logging.FileHandler(logfile)
    formatter = logging.Formatter(fmt=settings.LOG_FORMAT, datefmt=settings.DATE_FORMAT)
    file_handle.setFormatter(formatter)
    log = logging.getLogger()
    for handler in log.handlers:
        log.removeHandler(handler)
    log.addHandler(file_handle)
    log.setLevel(logging.DEBUG)
    return log



def time_now(aware=False):
    """Gets the regular time"""
    if aware:
        from django.utils import timezone

        return timezone.localtime(timezone.now())
    # naive datetime
    return datetime.now()


def time_from_now(date):
    """
    Gets timedelta compared to now
    Args:
        date: Datetime object to compare to now

    Returns:
        Timedelta object of difference between date and the current time.
    """
    try:
        diff = date - time_now()
    except (TypeError, ValueError):
        diff = date - time_now(aware=True)
    return diff


def datetime_format(date):
    """
    Takes a datetime object instance (e.g. from django's DateTimeField)
    and returns a string describing how long ago that date was.
    """
    year, month, day = date.year, date.month, date.day
    hour, minute, second = date.hour, date.minute, date.second
    now = datetime.now()

    if year < now.year:
        # another year
        timestring = str(date.date())
    elif date.date() < now.date():
        # another date, same year
        # put month before day because of FREEDOM
        timestring = "%02i-%02i %02i:%02i" % (month, day, hour, minute)
    elif hour < now.hour - 1:
        # same day, more than 1 hour ago
        timestring = "%02i:%02i" % (hour, minute)
    else:
        # same day, less than 1 hour ago
        timestring = "%02i:%02i:%02i" % (hour, minute, second)
    return timestring


def sub_old_ansi(text):
    """Replacing old ansi with newer evennia markup strings"""
    if not text:
        return ""
    text = text.replace("%r", "|/")
    text = text.replace("%R", "|/")
    text = text.replace("%t", "|-")
    text = text.replace("%T", "|-")
    text = text.replace("%b", "|_")
    text = text.replace("%cr", "|r")
    text = text.replace("%cR", "|[R")
    text = text.replace("%cg", "|g")
    text = text.replace("%cG", "|[G")
    text = text.replace("%cy", "|!Y")
    text = text.replace("%cY", "|[Y")
    text = text.replace("%cb", "|!B")
    text = text.replace("%cB", "|[B")
    text = text.replace("%cm", "|!M")
    text = text.replace("%cM", "|[M")
    text = text.replace("%cc", "|!C")
    text = text.replace("%cC", "|[C")
    text = text.replace("%cw", "|!W")
    text = text.replace("%cW", "|[W")
    text = text.replace("%cx", "|!X")
    text = text.replace("%cX", "|[X")
    text = text.replace("%ch", "|h")
    text = text.replace("%cn", "|n")
    return text

def highlight_words(text, caller):
    if not text:
        return ""
    lightlist = caller.db.highlightlist
    if not lightlist:
        return text
    for phrase, color in lightlist:
        text = text.replace(phrase, ("|"+ color + phrase + "|n"))
        return text

def strip_ansi(text):
    """Stripping out old ansi from a string"""
    from evennia.utils.ansi import strip_ansi

    text = strip_ansi(text)
    text = (
        text.replace("%r", "")
        .replace("%R", "")
        .replace("%t", "")
        .replace("%T", "")
        .replace("%b", "")
    )
    text = (
        text.replace("%cr", "")
        .replace("%cR", "")
        .replace("%cg", "")
        .replace("%cG", "")
        .replace("%cy", "")
    )
    text = (
        text.replace("%cY", "")
        .replace("%cb", "")
        .replace("%cB", "")
        .replace("%cm", "")
        .replace("%cM", "")
    )
    text = (
        text.replace("%cc", "")
        .replace("%cC", "")
        .replace("%cw", "")
        .replace("%cW", "")
        .replace("%cx", "")
    )
    text = text.replace("%cX", "").replace("%ch", "").replace("%cn", "")
    return text


def broadcast(txt, format_announcement=True):
    """Broadcasting a message to the server"""
    from evennia.server.sessionhandler import SESSION_HANDLER
    from evennia.scripts.models import ScriptDB

    if format_announcement:
        txt = "{wServer Announcement{n: %s" % txt
    txt = sub_old_ansi(txt)
    SESSION_HANDLER.announce_all(txt)
    try:
        events = ScriptDB.objects.get(db_key="Event Manager")
        events.add_gemit(txt)
    except ScriptDB.DoesNotExist:
        pass


def raw(text):
    """
    Escape text that is raw without resolving.
    """
    from evennia.utils.ansi import raw as evennia_raw

    if not text:
        return ""
    # get Evennia codes from the Arx-specific codes
    text = sub_old_ansi(text)
    # if any were turned into newlines, we substitute the code
    text = text.replace("\n", "|/")
    # escape all of them
    text = evennia_raw(text)
    return text


# noinspection PyProtectedMember
def post_roster_cleanup(entry):
    """
    Gets rid of past data for a roster entry from previous players.

    Args:
        entry: RosterEntry we're initializing
    """
    entry.player.nicks.clear()
    entry.character.nicks.clear()
    entry.player.attributes.remove("playtimes")
    entry.player.attributes.remove("rp_preferences")
    entry.player.attributes.remove("block_list")
    for character in entry.player.db.watching or []:
        watched_by = character.db.watched_by or []
        if entry.player in watched_by:
            watched_by.remove(entry.player)
    entry.player.attributes.remove("watching")
    entry.player.attributes.remove("hide_from_watch")
    entry.player.db.mails = []
    entry.player.db.readmails = set()
    entry.player.tags.remove("new_mail")
    entry.player.permissions.remove("Helper")
    disconnect_all_channels(entry.player)
    entry.character.tags.remove("given_starting_gear")
    post_roster_dompc_cleanup(entry.player)


def disconnect_all_channels(player):
    """Removes all channels from the player"""
    for channel in player.account_subscription_set.all():
        channel.disconnect(player)


def reset_to_default_channels(player):
    """
    Sets the player to only be connected to the default Info and Public channels
    Args:
        player: AccountDB object to reset
    """
    from typeclasses.channels import Channel

    disconnect_all_channels(player)
    required_channels = Channel.objects.filter(db_key__in=("Info", "Public"))
    for req_channel in required_channels:
        if not req_channel.has_connection(player):
            req_channel.connect(player)



def caller_change_field(caller, obj, field, value, field_name=None):
    """
    DRY way of changing a field and notifying a caller of the change.
    Args:
        caller: Object to msg the result
        obj: database object to have a field set and saved
        field (str or unicode): Text value to set
        value: value to set in the field
        field_name: Optional value to use for the field name
    """
    old = getattr(obj, field)
    setattr(obj, field, value)
    obj.save()
    field_name = field_name or field.capitalize()
    if len(str(value)) > 78 or len(str(old)) > 78:
        old = "\n%s\n" % old
        value = "\n%s" % value
    caller.msg("%s changed from %s to %s." % (field_name, old, value))



def lowercase_kwargs(*kwarg_names, **defaults):
    """
    Decorator for converting given kwargs that are list of strings to lowercase, and optionally appending a
    default value.
    """
    default_append = defaults.get("default_append", None)
    from functools import wraps

    def wrapper(func):
        """The actual decorator that we'll return"""

        @wraps(func)
        def wrapped(*args, **kwargs):
            """The wrapped function"""
            for kwarg in kwarg_names:
                if kwarg in kwargs:
                    kwargs[kwarg] = kwargs[kwarg] or []
                    kwargs[kwarg] = [ob.lower() for ob in kwargs[kwarg]]
                    if default_append is not None:
                        kwargs[kwarg].append(default_append)
            return func(*args, **kwargs)

        return wrapped

    return wrapper


def fix_broken_attributes(broken_object):
    """
    Patch to fix objects broken by broken formset for Attributes in django admin, where validation errors convert
    the Attributes to unicode.
    """
    from ast import literal_eval
    from evennia.utils.dbserialize import from_pickle

    for attr in broken_object.attributes.all():
        try:
            attr.value = from_pickle(literal_eval(attr.value))
        except (ValueError, SyntaxError) as err:
            print("Error for attr %s: %s" % (attr.key, err))
            continue

def color_check(val):
    # this quick utility checks to see if someone has selected a correct color code
    # is it an integer?
    try:
        val = int(val)
        if val > 0 and val < 555:
            return "xterm"
        else:
            return "invalid"
    except ValueError:
        # it's a string
        if len(val) > 2:
            return "invalid"
        else:
            if val[0] == "=":
                return "xterm"
            if len(val) > 1:
                return "invalid"
            else:
                val = val.lower()
                if val == "r" or val == "g" or val == "y" or val == "b" or val == "m" or val == "c" or val == "w":
                    return "ansi"
                else:
                    return "invalid"


def list_to_string(inlist, endsep="and", addquote=False):
    """
    This pretty-formats a list as string output, adding an optional
    alternative separator to the second to last entry.  If `addquote`
    is `True`, the outgoing strings will be surrounded by quotes.
    Args:
        inlist (list): The list to print.
        endsep (str, optional): If set, the last item separator will
            be replaced with this value. Oxford comma used for "and" and "or".
        addquote (bool, optional): This will surround all outgoing
            values with double quotes.
    Returns:
        liststr (str): The list represented as a string.
    Examples:
        ```python
         # no endsep:
            [1,2,3] -> '1, 2, 3'
         # with endsep=='and':
            [1,2,3] -> '1, 2, and 3'
         # with endsep=='that delicious':
            [7,8,9] -> '7, 8 that delicious 9'
         # with addquote and endsep
            [1,2,3] -> '"1", "2" and "3"'
        ```
    """
    if not endsep:
        endsep = ","
    elif endsep in ("and", "or") and len(inlist) > 2:
        endsep = ", " + endsep
    else:
        endsep = " " + endsep
    if not inlist:
        return ""
    if addquote:
        if len(inlist) == 1:
            return '"%s"' % inlist[0]
        return ", ".join('"%s"' % v for v in inlist[:-1]) + "%s %s" % (
            endsep,
            '"%s"' % inlist[-1],
        )
    else:
        if len(inlist) == 1:
            return str(inlist[0])
        return ", ".join(str(v) for v in inlist[:-1]) + "%s %s" % (endsep, inlist[-1])


def queryset_to_string(qset):
    """
    Gets a string representation of the queryset. We check plural class name for each object in the
    queryset, starting a new line & title to represent separate match categories.
    Args:
        qset (queryset): The pre-ordered queryset to print. If multiple ObjectDB classes, should
                         already be ordered by 'db_typeclass_path' as well.
    Returns:
        Example string: [Weapons] Sword of Killing; Stabbyknife
                        [Wearables] Sleek Catsuit; Fox-eared Scarf; Beaded Belt
    """
    class_name = None
    message = ""
    sep = ""
    for obj in qset:
        # noinspection PyProtectedMember
        plural_name = obj._meta.verbose_name_plural
        if plural_name != class_name:
            class_name = plural_name
            message += "\n|w[%s]|n " % class_name.title()
            sep = ""
        message += sep + str(obj)
        sep = "; "
    return message


def qslist_to_string(qslist):
    """
    Gets a string representation of multiple querysets in a list, separated by queryset classes.
    Args:
        qslist (list of querysets): Each queryset should be pre-ordered. If a qet contains
                                    multiple ObjectDB classes, should already be ordered by
                                    'db_typeclass_path' as well.
    Returns:
        Example string: [Weapons] Sword of Killing; Stabbyknife
                        [Wearables] Sleek Catsuit; Fox-eared Scarf; Beaded Belt
                        [Clues] Vixens are Evil
    """
    qslist = [ob.distinct() for ob in qslist if len(ob) > 0]
    message = ""
    if qslist:
        for qset in qslist:
            message += queryset_to_string(qset)
    return message


class CachedProperty(object):
    """
    Pretty similar to django's cached_property, but will be used for the CachedPropertiesMixin for models
    wiping their cached properties upon saving
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, "__doc__")
        self.name = name or func.__name__

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self.func(instance)
        return instance.__dict__[self.name]

    def __delete__(self, instance):
        instance.__dict__.pop(self.name, None)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class CachedPropertiesMixin(object):
    """Class that has a clear properties class method"""

    def clear_cached_properties(self):
        """Clear all cached properties from this object"""
        cls = self.__class__
        props = [ob for ob in cls.__dict__.values() if isinstance(ob, CachedProperty)]
        for prop in props:
            delattr(self, prop.func.__name__)

    def save(self, *args, **kwargs):
        super(CachedPropertiesMixin, self).save(*args, **kwargs)
        self.clear_cached_properties()


def a_or_an(word):

    if word[:1].lower() in ["a", "e", "i", "o", "u"]:
        return "an"

    return "a"


def commafy(string_list):
    if len(string_list) == 0:
        return "None"
    elif len(string_list) == 1:
        return string_list[0]
    elif len(string_list) == 2:
        return string_list[0] + " and " + string_list[1]
    else:
        return ", ".join(string_list[:-2] + [" and ".join(string_list[-2:])])


# noinspection PyPep8Naming
class classproperty(object):
    """Descriptor for making a property that always goes off the class, not the instance."""

    def __init__(self, getter):
        """
        Args:
            getter (function): the method that will become a class property
        """
        self.getter = getter

    def __get__(self, instance, owner):
        """

        Args:
            instance: instance of class or None, ignored
            owner: The class object itself

        Returns:
            Returns the result of calling self.getter with the class passed in, instead of 'self'
        """
        return self.getter(owner)


def get_full_url(url):
    """
    Gets the full url when given a partial, used for formatting links. For this to work
    properly, you should define your Site's url under the 'Sites' app in django's admin
    site.
    Args:
        url: A partial url from a few, like '/namespace/view/'

    Returns:
        A full url, like "http://www.example.com/namespace/view/"
    """
    from django.contrib.sites.models import Site

    return "http://%s%s" % (Site.objects.get_current(), url)
