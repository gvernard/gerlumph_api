from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, DetailView, ListView
#from django.db.models.query_utils import Q, Count
from django.db.models import Q, Count
from django.core.paginator import Paginator

from gerlumph_downloads.models import Downloads
from gerlumph_users.models import Users


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


class AdminDownloadUser(UserPassesTestMixin,TemplateView):
    template_name = 'gerlumph_downloads/admin_user_downloads.html'

    def test_func(self):
        return self.request.user.limitsandroles.is_admin

    def get(self, request, *args, **kwargs):
        other_user = Users.objects.get(id=self.kwargs.get('other_user'))

        # Paginator for downloads
        ordered_downloads = Downloads.objects.filter( Q(owner=other_user) ).order_by('-created_at')
        down_paginator = Paginator(ordered_downloads,50)
        down_page_number = request.GET.get('downloads-page',1)
        down_page = down_paginator.get_page(down_page_number)

        # Contribution plot
        plot = other_user.get_contribution_plot(ordered_downloads)
        
        context={'other_user':other_user,
                 'downloads_range': down_paginator.page_range,
                 'downloads': down_page,
                 'N_downloads_total': down_paginator.count,
                 'admin_page': False,
                 "plot": plot,
                 }
        return render(request, self.template_name, context=context)



class AdminDownloadList(UserPassesTestMixin,TemplateView):
    template_name = 'gerlumph_downloads/admin_all_downloads.html'

    def test_func(self):
        # Must return True for the user to pass, otherwise throws 403 Forbidden
        return self.request.user.limitsandroles.is_admin

    def get(self, request, *args, **kwargs):        
        users_with_downs = Users.objects.filter(downloads__isnull=False).distinct()
        all_downs = []
        n_downs = []
        for user in users_with_downs:
            downs = Downloads.objects.filter( Q(owner=user) )
            all_downs.append(downs)
            n_downs.append( downs.aggregate(N_maps=Count('maps')).get('N_maps') )

        
        zipped = list(zip(users_with_downs,n_downs,all_downs))

        # Paginator for downloads
        down_paginator = Paginator(zipped,50)
        down_page_number = request.GET.get('page',1)
        down_page = down_paginator.get_page(down_page_number)
      
        context={
            'downloads_range': down_paginator.page_range,
            'zipped_user_downs': zipped,
            'N_downloads_total': down_paginator.count,
        }
        return render(request, self.template_name, context=context)


    
