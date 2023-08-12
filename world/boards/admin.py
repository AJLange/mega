from django.contrib import admin
from world.boards.models import BulletinBoard, BoardPost

# Register your models here.

class BulletinBoardAdmin(admin.ModelAdmin):
    list_display = ("id","db_name")
    list_display_links  = ("id","db_name")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True

class BoardPostAdmin(admin.ModelAdmin):
    list_display = ("id","db_title", "posted_by")
    list_display_links  = ("id","db_title")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True


admin.site.register(BulletinBoard, BulletinBoardAdmin)
admin.site.register(BoardPost, BoardPostAdmin)
