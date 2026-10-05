from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, ListView


from gerlumph_maps.models import MagMaps


@method_decorator(login_required,name='dispatch')
class MapDetailView(DetailView):
    model = MagMaps
    template_name = 'gerlumph_maps/map_detail.html'
    context_object_name = 'map'
    
    def get_queryset(self):
        return MagMaps.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['icon'] = self.object.get_icon_url()
        context['sample'] = self.object.get_sample_url()
        context['mpd'] = self.object.get_mpd_url()

        return context

