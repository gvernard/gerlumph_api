from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F,Q,Count
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import TemplateView, DetailView, ListView
from django.urls import reverse,reverse_lazy
from django.core.paginator import Paginator
from django.core import serializers
from django.forms import formset_factory
from django.conf import settings
from django.apps import apps

from bootstrap_modal_forms.generic import (
    BSModalFormView,
    BSModalCreateView,
    BSModalUpdateView,
    BSModalDeleteView,
    BSModalReadView,
)
from bootstrap_modal_forms.mixins import is_ajax


import json
from urllib.parse import urlparse

from .forms import *

from gerlumph_users.models import Users
from gerlumph_tasks.models import Tasks



@method_decorator(login_required,name='dispatch')
class TaskListView(ListView):
    model = Tasks
    template_name = 'gerlumph_tasks/task_list.html'
    context_object_name = 'owner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
                
        if self.kwargs.get('admin'):
            admin = Users.getAdmin().first()
            owner = self.model.custom_manager.all_as_owner_only(admin)
            recipient = self.model.custom_manager.all_as_recipient_only(admin)
        else:
            #owner = self.model.accessible_objects.owned(self.request.user).exclude(task_type__exact='AcceptNewUser')
            #recipient = self.model.custom_manager.all_as_recipient(self.request.user).exclude(task_type__exact='ResolveDuplicates')
            owner_only = self.model.custom_manager.all_as_owner_only(self.request.user).exclude(task_type__exact='AcceptNewUser')
            recipient_only = self.model.custom_manager.all_as_recipient_only(self.request.user)
            both = self.model.custom_manager.both_owner_recipient(self.request.user)
            owner = owner_only|both.filter(status="C")
            recipient = recipient_only|both.filter(status="P")
            

        date_check = timezone.now() - timezone.timedelta(days=10)
        N_old = owner.filter( Q(status='C') & Q(completed_at__lt=date_check) ).count()
        #print(date_check,N_old)
        
        o_paginator = Paginator(owner,50)
        o_page_number = self.request.GET.get('tasks_owned-page',1)

        r_paginator = Paginator(recipient,50)
        r_page_number = self.request.GET.get('tasks_recipient-page',1)
        if 'admin' in self.kwargs.keys():
            admin_page = True
        else:
            admin_page = False

        context = {'N_owner': o_paginator.count,
                   'owner_range': o_paginator.page_range,
                   'owner': o_paginator.get_page(o_page_number),
                   'N_recipient': r_paginator.count,
                   'recipient_range': r_paginator.page_range,
                   'recipient': r_paginator.get_page(r_page_number),
                   'admin_page': admin_page,
                   'N_old': N_old
                   }
        return context

    def get(self, *args, **kwargs):
        if self.kwargs.get('admin') and not self.request.user.limitsandroles.is_admin:
            return TemplateResponse(self.request,'simple_message.html',context={'message':'You are not authorized to view this page.'})
        return super(TaskListView,self).get(*args, **kwargs)

    
@method_decorator(login_required,name='dispatch')
class TaskDetailOwnerView(BSModalReadView):
    model = Tasks
    template_name = 'gerlumph_tasks/task_detail_owner.html'
    context_object_name = 'task'

    def get_queryset(self):
        if self.kwargs.get('admin'):
            return self.model.accessible_objects.owned(Users.getAdmin().first())
        else:
            return self.model.accessible_objects.owned(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        
        context['allowed'] = ' or '.join( map(str.upper,task.allowed_responses()) )

        # Queryset of objects in the task
        #objects = getattr(lenses.models,task.cargo["object_type"]).objects.filter(pk__in=task.cargo["object_ids"])
        #context['objects'] = objects
        context['objects'] = []

        # Object type (singular or plural) for the objects in the task
        if objects.count() > 1:
            object_type = getattr(lenses.models,task.cargo["object_type"])._meta.verbose_name_plural.title()
        else:
            object_type = getattr(lenses.models,task.cargo["object_type"])._meta.verbose_name.title()
        context['object_type'] = object_type

        #context['hf'] = self.object.heard_from().annotate(name=F('recipient__username')).values('name','response','created_at','response_comment')
        #context['nhf'] = self.object.not_heard_from().values_list('recipient__username',flat=True)
        context['responses'] = task.get_all_responses().annotate(name=F('recipient__username')).values('name','response','created_at','response_comment')
        return context



 
    
@method_decorator(login_required,name='dispatch')
class TaskDetailRecipientView(BSModalFormView):
    template_name = 'gerlumph_tasks/task_detail_recipient.html'
    success_message = 'Success: Your response has been recorded.'
    success_url = reverse_lazy('gerlumph_tasks:tasks-list')
    task = None

    # def get_template_names(self):
    #     if self.task.task_type == 'RequestUpdate':
    #         return ['sled_tasks/task_detail_request_update_recipient.html']
    #     else:
    #         return ['sled_tasks/task_detail_recipient.html']
    
    def get_initial(self):
        # Check if a response is already in the database  
        try:
            if self.kwargs.get('admin'):
                db_response = self.task.recipients.through.objects.get(task__exact=self.task.id,recipient__username=Users.getAdmin().first().username)
            else:
                db_response = self.task.recipients.through.objects.get(task__exact=self.task.id,recipient__username=self.request.user.username)
        except task.DoesNotExist:
            db_response = None
        initial = {}
        if db_response.response:
            initial['response'] = db_response.response
            if db_response.response_comment:
                initial['response_comment'] = db_response.response_comment
        return initial
       
    def get_form_class(self):
        task_id = self.kwargs['pk']
        
        if self.kwargs.get('admin'):
            self.task = Tasks.custom_manager.all_as_recipient(Users.getAdmin().first()).get(id=task_id)
        else:
            self.task = Tasks.custom_manager.all_as_recipient(self.request.user).get(id=task_id)
            
        if self.task.task_type == "CedeOwnership":
            return CedeOwnershipForm
        elif self.task.task_type == "DeleteObject":
            return DeleteObjectForm
        elif self.task.task_type == "AcceptNewUser":
            return AcceptNewUserForm
        else:
            pass
        
    def get_form(self,form_class=None):
        form = super().get_form(form_class)
        if 'response' in form.initial:
            form.fields["response"].disabled = True
        if 'response_comment' in form.initial:
            form.fields["response_comment"].disabled = True        
        return form 
    
    def get_context_data(self, **kwargs):
        context = super(TaskDetailRecipientView,self).get_context_data(**kwargs)

        context['task'] = self.task

        # Comment from task sender
        comment = ''
        if 'comment' in self.task.cargo:
            comment = self.task.cargo['comment']
        context['comment'] = comment
            
        # Queryset of objects in the task
        #objects = getattr(lenses.models,self.task.cargo["object_type"]).objects.filter(pk__in=self.task.cargo["object_ids"])
        #context['objects'] = objects
        #context['objects'] = []

        # Object type (singular or plural) for the objects in the task
        #if objects.count() > 1:
        #    object_type = getattr(lenses.models,self.task.cargo["object_type"])._meta.verbose_name_plural.title()
        #else:
        #    object_type = getattr(lenses.models,self.task.cargo["object_type"])._meta.verbose_name.title()
        #context['object_type'] = object_type
            
        #context['admin'] = self.kwargs.get('admin')
        try:
            if self.kwargs.get('admin'):
                db_response = self.task.recipients.through.objects.get(task__exact=self.task.id,recipient__username=Users.getAdmin().first().username)
            else:
                db_response = self.task.recipients.through.objects.get(task__exact=self.task.id,recipient__username=self.request.user.username)
        except task.DoesNotExist:
            db_response = None
        context['db_response'] = db_response

        return context

    def form_valid(self,form):
        if not is_ajax(self.request.META):
            response = self.request.POST.get('response')
            response_comment = self.request.POST.get('response_comment')
            messages.add_message(self.request,messages.SUCCESS,self.success_message)
            if self.kwargs.get('admin'):
                self.task.registerAndCheck(Users.getAdmin().first(),response,response_comment)
                return HttpResponseRedirect(reverse('gerlumph_tasks:tasks-list-admin'))
            else:
                self.task.registerAndCheck(self.request.user,response,response_comment)
                return HttpResponseRedirect(reverse('gerlumph_tasks:tasks-list'))
        else:
            return super(TaskDetailRecipientView,self).form_valid(form)


    
@method_decorator(login_required,name='dispatch')
class TaskDeleteView(BSModalDeleteView):
    model = Tasks
    template_name = 'gerlumph_tasks/task_delete.html'
    success_message = 'Success: Task was deleted.'
    context_object_name = 'task'
    success_url = reverse_lazy('gerlumph_tasks:tasks-list')

    def get_queryset(self):
        #return self.model.objects.filter( Q(owner=self.request.user) and Q(status='C') )
        return self.model.objects.filter( Q(owner=self.request.user) )


