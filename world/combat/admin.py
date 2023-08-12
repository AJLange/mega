from django.contrib import admin
from world.combat.models import Weapon, BusterList, GenericAttack

class WeaponAdmin(admin.ModelAdmin):
    list_display = ("id", "db_name","db_class","db_type_1", "db_type_2", "db_type_3")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created", "^db_name"]
    save_as = True
    save_on_top = True
    list_select_related = True

class BusterListAdmin(admin.ModelAdmin):
    list_display = ("id","db_thief", "db_name", "db_class","db_type_1", "db_type_2", "db_type_3")
    list_display_links  = ("id","db_thief","db_name")
    
    search_fields = ["^db_date_created", "^db_thief", "^db_name"]
    save_as = True
    save_on_top = True
    list_select_related = True

class GenericAttackAdmin(admin.ModelAdmin):
    list_display = ("id","db_name", "db_class")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created"]
    save_as = True
    save_on_top = True
    list_select_related = True



admin.site.register(Weapon, WeaponAdmin)
admin.site.register(BusterList, BusterListAdmin)
admin.site.register(GenericAttack, GenericAttackAdmin)


