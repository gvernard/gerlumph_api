from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, ListView


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

        maps = self.object.maps

        icons = []
        for mm in maps:
            icons.append( mm.get_icon_url() )

        context["list"] = list(zip(maps,icons))
        
        return context

