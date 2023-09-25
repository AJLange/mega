from django.contrib import admin
from world.roster.models import RosterEntry, GameRoster

class GameRosterAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")


class RosterAdmin(admin.ModelAdmin):
    list_display = ("id","db_chracter",)
    list_display_links  = ("id","db_character")


admin.site.register(GameRoster, GameRosterAdmin)
admin.site.register(RosterEntry, RosterAdmin)