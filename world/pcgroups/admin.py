from django.contrib import admin
from world.pcgroups.models import Squad, PlayerGroup

class SquadAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True

class PlayerGroupAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True

admin.site.register(Squad, SquadAdmin)
admin.site.register(PlayerGroup, PlayerGroupAdmin)