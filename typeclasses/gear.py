from typeclasses.objects import Object

class Item(Object):
    '''
    Any random simple object created by a player. 
    An item has a desc, but that's it.

    '''
    def at_object_creation(self):
        self.db.desc = "This is a nondescript object."


class Pet(Object):
    '''
    A pet is a type of object that is a friend.

    Players cannot create these; they require
    staff for the time being.
    '''
    def at_object_creation(self):
        self.db.desc = "This is a pet."
