from django.contrib import admin
from world.requests.models import Request, RequestResponse

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



admin.site.register(Request, RequestAdmin)
admin.site.register(RequestResponse, RequestResponseAdmin)
