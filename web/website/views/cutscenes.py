from django.conf import settings
from django.views.generic import TemplateView

import evennia
from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB
from evennia.utils import class_from_module

class CutsceneIndexView(TemplateView):
   

    # Tell the view what HTML template to use for the page
    template_name = "website/cutscenes.html"
    page_title = "Cutscenes"
    access_type = "view"
    # This method tells the view what data should be displayed on the template.
    def get_context_data(self, **kwargs):
        """
        Not using this, just preserving it for now.

        """
        # Always call the base implementation first to get a context object
        context = super().get_context_data(**kwargs)


        return context