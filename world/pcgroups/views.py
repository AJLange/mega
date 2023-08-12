from django.shortcuts import render
from evennia import ObjectDB


def group(request):
    group_list = ObjectDB.objects.filter(db_typeclass_path__contains="PlayerGroup") # filter by Character typeclass, since ObjectDB contains all objects
    squad_list = ObjectDb.objects.filter(db_typeclass_path__contains="Squad")




    context = {
        'group_list': group_list,
        'squad_list': squad_list
    }

    return render(request, "group/group.html", context)