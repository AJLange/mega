from django.contrib import admin
from world.requests.models import Request, RequestResponse, Keyword, File, Topic

# Register your models here.

class RequestAdmin(admin.ModelAdmin):
    list_display = ("id", "db_title", "type",)
    list_display_links  = ("id",)
    
    search_fields = ["db_key", "^db_date_created", "^db_title"]
    save_as = True
    save_on_top = True
    list_select_related = True


class RequestResponseAdmin(admin.ModelAdmin):
    list_display = ("id",)
    list_display_links  = ("id",)
    
    search_fields = ["db_key", "^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True

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

admin.site.register(Request, RequestAdmin)
admin.site.register(RequestResponse, RequestResponseAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Topic,TopicAdmin)
