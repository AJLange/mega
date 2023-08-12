from django.contrib import admin
from world.roster.models import Roster, PlayerAccount

class PlayerAccountAdmin(admin.ModelAdmin):
    list_display = ("id","db_name" ,"email")
    list_display_links  = ("id","db_name","email")


class RosterAdmin(admin.ModelAdmin):
    list_display = ("id","db_name",)
    list_display_links  = ("id","db_name",)


admin.site.register(PlayerAccount, PlayerAccountAdmin)
admin.site.register(Roster, RosterAdmin)