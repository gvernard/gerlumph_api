from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.views.generic import TemplateView,DetailView
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.http import Http404
from django.utils.translation import gettext as _
from django.db.models import Q

from bootstrap_modal_forms.generic import (
    BSModalFormView,
    BSModalUpdateView,
    BSModalDeleteView,
    BSModalReadView,
)
from operator import attrgetter
from itertools import chain

from gerlumph_users.models import Users
from gerlumph_tasks.models import Tasks
#, MagMaps
from .forms import UsersSearchForm,UserUpdateForm
from .decorators import admin_access_only


@method_decorator(login_required,name='dispatch')
class UserQueryView(TemplateView):
    model = Users
    template_name = 'gerlumph_users/user_query.html'

    def user_query(self,cleaned_data):
        search_term = cleaned_data['search_term']
        if search_term:
            #users = Users.objects.filter(Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term) | Q(email__icontains=search_term)).select_related("limitsandroles")
            users = Users.objects.filter(Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term) | Q(email__icontains=search_term))
        else:
            users = Users.objects.all()

        '''
        role = cleaned_data["role"]
        if role == 'SuperAdmin':
            users = users.filter(limitsandroles__is_super_admin=True)
        elif role == "Admin":
            users = users.filter(limitsandroles__is_admin=True)
        elif role == "Inspector":
            users = users.filter(limitsandroles__is_inspector=True)
        elif role == "active":
            users = users.filter(is_active=True)
        elif role == "inactive":
            users = users.filter(is_active=False)
        '''
        
        users = users.exclude(username__in=['admin','AnonymousUser'])
        
        paginator = Paginator(users,50)
        users_page = paginator.get_page(cleaned_data['page'])
        users_count = paginator.count
        users_range = paginator.page_range

        return users_page,users_range,users_count

    def get_context(self,form):
        if form.is_valid():
            users_page,users_range,users_count = self.user_query(form.cleaned_data)
            context = {'N_users_total': users_count,
                       'users_range': users_range,
                       'users': users_page,
                       'form': form}
        else:
            context = {'N_users_total': 0,
                       'users_range': [],
                       'users': None,
                       'form': form}
        return context

        
    
    def get(self, request, *args, **kwargs):
        if request.GET:
            form = UsersSearchForm(request.GET)
        else:
            form = UsersSearchForm(initial={'role':'active'})
        context = self.get_context(form)
        return self.render_to_response(context)

    
    def post(self, request, *args, **kwargs):
        form = UsersSearchForm(data=request.POST)
        context = self.get_context(form)
        return self.render_to_response(context)
    


@method_decorator(login_required,name='dispatch')
class UserVisitCard(DetailView):
    model = Users
    template_name = 'gerlumph_users/user_visit_card.html'
    context_object_name = 'gerlumph_user'

    def get_queryset(self):
        return Users.objects.all()
    
    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        queryset = self.get_queryset().filter(username=username)
        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj



    
@method_decorator(login_required,name='dispatch')
class UserProfileView(TemplateView):
    template_name = 'gerlumph_users/user_index.html'

    def get(self, request, *args, **kwargs):
        user = request.user

        # get pending confirmation tasks
        #pending_tasks = list(ConfirmationTask.custom_manager.pending_for_user(user).exclude(task_type__in=['AcceptNewUser']))
        #N_tasks = len(pending_tasks)
   
        # Get owned objects
        owned_objects = user.getOwnedObjects()

        '''
        # Paginator for magmaps
        ordered_lenses = owned_objects["Lenses"].order_by('-created_at')
        lenses_paginator = Paginator(ordered_lenses,50)
        lenses_page_number = request.GET.get('lenses-page',1)
        lenses_page = lenses_paginator.get_page(lenses_page_number)
        '''
        

        #recipient = ConfirmationTask.custom_manager.all_as_recipient(self.request.user)

 
        context={'user':user,
                 #'pending_tasks':pending_tasks,
                 #'N_tasks': N_tasks,
                 #'lenses_range': lenses_paginator.page_range,
                 #'lenses': lenses_page,
                 #'N_imagings_total': imagings_paginator.count,
                 'admin_page': False,
                 }
        return render(request, self.template_name, context=context)

    

@method_decorator(login_required,name='dispatch')
class UserUpdateView(BSModalUpdateView):
    model = Users
    template_name = 'gerlumph_users/user_update.html'
    form_class = UserUpdateForm
    success_message = 'Success: your profile was updated.'
    success_url = reverse_lazy('gerlumph_users:user-profile')





@method_decorator(admin_access_only,name='dispatch')
@method_decorator(login_required,name='dispatch')
class UserAdminView(TemplateView):
    template_name = 'gerlumph_users/user_admin.html'
    
    def get(self, request, *args, **kwargs):
        user = request.user

        admin = Users.getAdmin().first()
        print(admin)
        
        # get pending tasks
        pending_tasks = list(Tasks.custom_manager.pending_for_user(admin))
        N_tasks = len(pending_tasks)
        N_owned = Tasks.custom_manager.all_as_owner_only(admin).count()
        N_recipient = Tasks.custom_manager.all_as_recipient_only(admin).count()
        N_tasks_all = N_owned + N_recipient
             
        context={'user': user,
                 'hash': self.kwargs.get('hash'),        # Open accordion div
                 'pending_tasks':pending_tasks,
                 'N_tasks': N_tasks,
                 'N_tasks_all': N_tasks_all,
                 'admin_page': True,
                 }
        return render(request, self.template_name, context=context)
