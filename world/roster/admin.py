from django.contrib import admin
from world.roster.models import GameRoster

class GameRosterAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")


admin.site.register(GameRoster, GameRosterAdmin)
