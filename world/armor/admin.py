from django.contrib import admin
from world.armor.models import Capability, ArmorMode

# Register your models here.

class CapabilityAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True

class ArmorModeAdmin(admin.ModelAdmin):
    list_display = ("id","db_name", "db_swap")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True


admin.site.register(Capability, CapabilityAdmin)
admin.site.register(ArmorMode, ArmorModeAdmin)
