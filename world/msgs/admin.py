from django.contrib import admin
from world.msgs.models import Mail

class MailAdmin(admin.ModelAdmin):
    list_display = ("id","db_title", "db_sender", "db_reciever","db_date_created")
    list_display_links  = ("id","db_title")
    
    search_fields = ["^db_date_created",]
    save_as = True
    save_on_top = True
    list_select_related = True


admin.site.register(Mail, MailAdmin)


