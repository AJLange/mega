from django.contrib import admin
from world.radio.models import Frequency

class RadioAdmin(admin.ModelAdmin):
    list_display = ("id","db_freq", "db_name")
    list_display_links  = ("id","db_freq", "db_name")
    
    search_fields = ["db_freq", "db_name"]
    save_as = True
    save_on_top = True
    list_select_related = True


admin.site.register(Frequency)
