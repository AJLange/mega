from django.contrib import admin
from world.files.models import File, Keyword,Topic

# Register your models here.

class FileAdmin(admin.ModelAdmin):
    list_display = ("id","db_title")
    list_display_links  = ("id",)
    
    search_fields = ["id","db_title", "^db_date_created"]
    save_as = True
    save_on_top = True
    list_select_related = True

class TopicAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id",)
    
    search_fields = ["db_name"]
    save_as = True
    save_on_top = True
    list_select_related = True

class KeywordAdmin(admin.ModelAdmin):
    list_display = ("db_keyword",)
    list_display_links  = ("db_keyword",)
    
    search_fields = ["db_key",]
    save_as = True
    save_on_top = True
    list_select_related = True

admin.site.register(File, FileAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Topic, TopicAdmin)

