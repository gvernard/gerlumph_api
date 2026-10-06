from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, ListView
from django.db.models.query_utils import Q

from gerlumph_downloads.models import Downloads


@method_decorator(login_required,name='dispatch')
class DownloadDetailView(DetailView):
    model = Downloads
    template_name = 'gerlumph_downloads/download_detail.html'
    context_object_name = 'download'
    
    def get_queryset(self):
        return self.model.objects.filter( Q(owner=self.request.user) )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        maps = self.object.maps.all()

        icons = []
        for mm in maps:
            icons.append( mm.get_file_url("icon.png") )

        context["list"] = list(zip(maps,icons))
        
        return context

