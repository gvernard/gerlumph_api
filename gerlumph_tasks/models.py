from django.db import models,connection
from django.utils import timezone
from django.utils.html import strip_tags
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core import serializers
from django.core.files.storage import default_storage
from django.core.files import File
from django.urls import reverse
from django import forms
from django.db.models import Q,F,Count,CharField
from django.apps import apps
from django.conf import settings
from django.template.loader import get_template
from django.template.response import TemplateResponse


import abc
import json
import os
import string
import random
import shutil

from gerlumph_users.models import Users
from gerlumph_limits.models import LimitsAndRoles



class TaskManager(models.Manager):
    def pending_for_user(self,user):
        return super().get_queryset().filter(status='P').filter(Q(owner=user)|Q(recipients__username=user.username))

    def completed_for_user(self,user):
        return super().get_queryset().filter(status='C').filter(Q(owner=user)|Q(recipients__username=user.username))

    def all_as_recipient(self,user):
        return super().get_queryset().filter(Q(recipients__username=user.username))

    def all_as_owner_only(self,user):
        return super().get_queryset().filter(owner=user).exclude(Q(recipients__username=user.username))
    
    def all_as_recipient_only(self,user):
        return super().get_queryset().filter(Q(recipients__username=user.username)).exclude(owner=user)

    def both_owner_recipient(self,user):
        return super().get_queryset().filter( Q(recipients__username=user.username) & Q(owner=user) )

    
                
class Tasks(models.Model):
    """
    The Task object.

    Attributes:
        task_name (str): the name of the task to perform.
        status (`enum`): completed if all the users have responded, otherwise pending.
        cargo (json): a JSON object that carries information necessary to complete the task once all responses have been received.
        recipients (`QuerySet`): A set of Users.

    Todo:
        - Associate the task name to a class (classes of task types will need to be implemented first). 
    """
    owner = models.ForeignKey(Users,
                              on_delete=models.CASCADE,
                              help_text='A GERLUMPH user who created this task.')
    created_at = models.DateTimeField(auto_now_add=True,help_text="The date and time when the task was first created.")
    completed_at = models.DateTimeField(blank=True,null=True,help_text="The date and time when the task was completed.")

    # The task types MUST match 1-to-1 the proxy models below
    TaskTypeChoices = (
        #('CedeOwnership','Cede ownership'),
        #('DeleteObject','Delete public object'),
        ('AcceptNewUser','Accept new user'),
    )
    task_type = models.CharField(max_length=100,
                                 choices=TaskTypeChoices,
                                 help_text="The name of the task to perform.") 
    StatusTypeChoices = (
        ("P",'Pending'),
        ("C",'Completed')
    )
    status = models.CharField(max_length=1,
                              choices=StatusTypeChoices,
                              default="P",
                              help_text="Status of the task: 'Pending' (P) or 'Completed' (C).",)
    cargo = models.JSONField(help_text="A json object holding any variables that will be executed upon completion of the task.")
    recipients = models.ManyToManyField(
        Users,
        related_name='tasks_as_recipient',
        through='TaskResponse',
        through_fields=('task','recipient'),
        help_text="A many-to-many relationship between Tasks and Users that will need to respond."
    )
    recipient_names = []

    custom_manager = TaskManager()
    objects = models.Manager()
    
    class Meta():
        db_table = "tasks"
        verbose_name = "task"
        verbose_name_plural = "tasks"
        ordering = ["-status","-completed_at"]
        # constrain the number of recipients?
        
    def __init__(self, *args, **kwargs):
        super(Tasks,self).__init__(*args, **kwargs)
        subclass_found = False
        for _class in Tasks.__subclasses__():
            if self.task_type == _class.__name__:
                self.__class__ = _class
                subclass_found = True
                break
        if not subclass_found:
            raise ValueError(task_type)

    def __str__(self):
        return '%s_%s' % (self.task_type,str(self.id))

    def get_absolute_url(self):
        if self.owner.is_superuser: # This refers to the django user 'admin'
            return reverse('gerlumph_tasks:tasks-detail-admin-owner',kwargs={'pk':self.id})
        else:
            return reverse('gerlumph_tasks:tasks-detail-owner',kwargs={'pk':self.id})

    def create_task(sender,users,task_type,cargo):
        """
        Creates a task and assigns the recipients (list of users) to it via a many-to-many relation.

        It also invites the recipients by sending them a link via email.

        Args:
            sender (`User`): An instance of a `User` object.
            users (`QuerySet`): A queryset of User objects.
            task_type (str): The name of the task to perform once all users have responded.
            cargo (JSON): a JSON object with information required to complete the task.

        Returns:
            bool: True if the given user is the owner, False otherwise.
        """
        task = Tasks(owner=sender,task_type=task_type,cargo=cargo)
        task.save()
        task.recipients.set(users)
        task.save()
        task.recipient_names = list(users.values_list('username',flat=True))
        #print('task created: ',task.recipients.all())
        task.inviteRecipients(task.recipients.all())
        return task

    def load_task(task_id):
        """
        Loads a task based on the given id.

        If the task exists it returns it and sets the recipient_names variables, otherwise it returns None.

        Args:
            task_id (int): An integer representing the task id.

        Returns:
            Tasks object: if successful, otherwise None.
        """
        try:
            task = Tasks.objects.get(pk=task_id)
            task.recipient_names = list(task.recipients.values_list('username',flat=True))
        except Tasks.DoesNotExist:
            task = None
        return task

    def inviteRecipients(self,users):
        """
        Emails list of recipients to inform/remind them that a task requires their response

        Args:
            recipients (`QuerySet`): A queryset of User objects.
        """
        site = Site.objects.get_current()
        subject = 'SLED: Response to %s task required' % self.task_type
        from_email = 'sled-no-reply@sled.amnh.org'
        
        for user in users:
            html_message = get_template('emails/task_notification.html')
            mycontext = {
                'first_name': user.first_name,
                'task_type': self.task_type,
                'protocol': 'https',
                'domain': site.domain,
                'task_url': reverse('gerlumph_tasks:tasks-list')
            }
            html_message = html_message.render(mycontext)
            plain_message = strip_tags(html_message)
            recipient_email = user.email
            send_mail(subject,plain_message,from_email,[recipient_email],html_message=html_message)
            
    def get_all_recipients(self):
        """
        Gets all the recipients of the task. 
         
        Returns:
            A QuerySet with User objects.
        """
        return self.recipients.all()

    def get_all_responses(self):
        """
        Gets all the responses for the task. 
         
        Returns:
            A QuerySet with TaskResponse objects.
        """
        return self.recipients.through.objects.filter(task__exact=self.id)

    def not_heard_from(self):
         """
         Checks which recipients have not responded yet. 
         
         Returns:
             A QuerySet with TaskResponse objects.
         """
         return self.recipients.through.objects.filter(task__exact=self.id,response__exact='')

    def heard_from(self):
         """
         Checks which recipients have already responded. 
         
         Returns:
             A QuerySet with TaskResponse objects.
         """
         return self.recipients.through.objects.filter(task__exact=self.id).exclude(response__exact='')

    def registerResponse(self,user,response,comment):
        """
        Registers the given users response to the task
        """
        if user not in self.recipients.all():
            raise ValueError(self.recipient_names,user.username) # Need custom exception here
        if response not in self.allowed_responses(): 
            raise ValueError(response) # Need custom exception here
        self.recipients.through.objects.filter(task=self,recipient=user).update(response=response,response_comment=comment,created_at=timezone.now())
        #self.finalizeTask()
        #self.recipients.through.objects.filter(task=self,recipient=user).update(response='',response_comment=comment)
        

    def registerAndCheck(self,user,response,comment):
        """
        Registers the given recipients response and checks if all recipients have replied. If yes, calls finalizeTask and updates the status to completed.
        """
        self.registerResponse(user,response,comment)
        nhf = self.not_heard_from()
        if nhf.count() == 0:
            self.finalizeTask()
            self.status = "C"
            self.save()


    # To be overwritten by the proxy models
    #@property
    #@abc.abstractmethod
    def allowed_responses(self):
        pass

    # To be overwritten by the proxy models
    #@abc.abstractmethod
    def finalizeTask(self):
        pass


    
class TaskResponse(models.Model):
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    # response: just yes or no, pre-defined in database model.
    response = models.CharField(max_length=10000, help_text="The response of a given user to a given task.")
    #there is a strange bug where it complains about response_comment being too long (>100) even though the max length was 1000
    # so I have changed it to 1001 and forced the migration fixing the issue on my local server
    response_comment = models.CharField(max_length=10000,
                                        help_text="A comment (optional) from the recipient on the given response.",
                                        #validators=[validate_language],
                                        )



class AcceptNewUser(Tasks):
    class Meta:
        proxy = True

    def allowed_responses(self):
        return ['yes','no']

    def finalizeTask(self):
        # There is only one recipient to get a response from for this task
        response = self.heard_from().get().response
        task_owner = Users.objects.get(id=self.owner.id) # needs to be a query set
        site = Site.objects.get_current()
        if response == 'yes':
            task_owner.is_active = True
            LimitsAndRoles.objects.create(user=task_owner)
            task_owner.save()
            subject = 'Welcome to GERLUMPH'
            html_message = get_template('emails/successful_registration.html')
            mycontext = {
                'first_name': task_owner.first_name,
                'last_name': task_owner.last_name,
                'protocol': 'https',
                'domain': site.domain,
                'response': self. heard_from().get().response_comment,
                'user_url': task_owner.get_absolute_url(),
                'coc_url': '', # reverse('grelumph_guide:sled-coc'),
                'username': task_owner.username,
            }
            html_message = html_message.render(mycontext)
            plain_message = strip_tags(html_message)
        else:
            subject = 'GERLUMPH: Unsuccessful registration'
            html_message = get_template('emails/unsuccessful_registration.html')
            mycontext = {
                'first_name': task_owner.first_name,
                'last_name': task_owner.last_name,
                'response':self. heard_from().get().response_comment
            }
            html_message = html_message.render(mycontext)
            plain_message = strip_tags(html_message)

        # Send email to user with the response
        user_email = task_owner.email
        from_email = 'gerlumph-no-reply@gerlumph.amnh.org'
        send_mail(subject,plain_message,from_email,[user_email],html_message=html_message)
            

'''
class DeleteObject(Tasks):
    class Meta:
        proxy = True
        
    def allowed_responses(self):
        return ['yes','no']

    def finalizeTask(self):
        responses = self.heard_from().annotate(name=F('recipient__username')).values_list('response',flat=True)
        
        from . import Users
        admin = Users.getAdmin().first()
        if len(set(responses)) == 1 and responses[0] == 'yes':
            #cargo = json.loads(self.cargo)
            #getattr(.models,self.cargo['object_type']).objects.filter(pk__in=self.cargo['object_ids']).delete()
            objs = apps.get_model(app_label="lenses",model_name=self.cargo['object_type']).objects.filter(pk__in=self.cargo['object_ids'])
            notify.send(sender=admin,
                        recipient=self.owner,
                        verb='DeleteObjectsAcceptedNote',
                        level='success',
                        timestamp=timezone.now(),
                        action_object=self)

            if self.cargo['object_type'] != 'Collection':
                uqset = self.owner.get_collection_owners(objs)
                users = list(set( uqset ))
                for u in users:
                    self.owner.remove_from_third_collections(objs,u)

            if self.cargo['object_type'] != 'Lenses':
                objs.delete()
            else:

                ### Unfollow lens ####################################################################
                for lens in objs:
                    lens_followers = followers(lens)
                    for user in lens_followers:
                        unfollow(user,lens,send_action=False)
                    
                ### Remove these lenses from any linked papers
                qset = apps.get_model(app_label="lenses",model_name='Paper').objects.filter(lenses_in_paper__id__in=self.cargo['object_ids'])
                for paper in qset:
                    paper.lenses_in_paper.remove(*objs)
                
                ### Delete linked data: Redshifts, Imaging, Spectrum, and Catalogue
                for user,lenses_ids in self.cargo['users_lenses'].items():
                    print("For user: ",user)
                    qset = apps.get_model(app_label="lenses",model_name='Redshift').objects.filter(Q(access_level="PUB") & Q(lens__id__in=lenses_ids) & Q(owner__username=user))
                    print(qset)
                    qset.delete()
                    qset = apps.get_model(app_label="lenses",model_name='Imaging').objects.filter(Q(access_level="PUB") & Q(lens__id__in=lenses_ids) & Q(owner__username=user))
                    print(qset)
                    qset.delete()
                    qset = apps.get_model(app_label="lenses",model_name='Spectrum').objects.filter(Q(access_level="PUB") & Q(lens__id__in=lenses_ids) & Q(owner__username=user))
                    print(qset)
                    qset.delete()
                    qset = apps.get_model(app_label="lenses",model_name='Catalogue').objects.filter(Q(access_level="PUB") & Q(lens__id__in=lenses_ids))
                    qset.delete()
                    print(qset)

                objs.delete()
                
                    
        else:
            notify.send(sender=admin,
                        recipient=self.owner,
                        verb='DeleteObjectsRejectedNote',
                        level='error',
                        timestamp=timezone.now(),
                        action_object=self)

            
class CedeOwnership(Tasks):
    class Meta:
        proxy = True

    def allowed_responses(self):
        return ['yes','no']

    def finalizeTask(self,**kwargs):
        # Here, only one recipient to get a response from
        response = self.heard_from().get().response
        heir = self.get_all_recipients()[0]
        if response == 'yes':
            #cargo = json.loads(self.cargo)
            #objs = getattr(lenses.models,self.cargo['object_type']).objects.filter(pk__in=self.cargo['object_ids'])
            object_type = self.cargo['object_type']
            model_ref = apps.get_model(app_label="lenses",model_name=object_type)
            objs = model_ref.objects.filter(pk__in=self.cargo['object_ids'])
            pri = []
            pub = []
            for obj in objs:
                obj.owner=heir
                obj.save()
                if obj.access_level == 'PRI':
                    pri.append(obj)
                else:
                    pub.append(obj)

            # Heir to unfollow any of the inherited objects
            if object_type == 'Lenses':
                set_followed = set(following(heir,Lenses))
                set_lenses = set(objs)
                intersection = list(set_followed.intersection(set_lenses))
                if len(intersection) > 0:
                    for lens in intersection:
                        unfollow(heir,lens)
                    ad_col = AdminCollection.objects.create(item_type=object_type,myitems=intersection)
                    notify.send(sender=heir,
                                recipient=heir,
                                verb='HeirUnfollowNote',
                                level='warning',
                                timestamp=timezone.now(),
                                action_object=ad_col)
                    
            # Handle public objects
            if pub and object_type != 'SledGroup':
                from . import Users
                ad_col = AdminCollection.objects.create(item_type=object_type,myitems=pub)
                action.send(self.owner,target=Users.getAdmin().first(),verb='CedeOwnershipHome',
                            level='info',action_object=ad_col,previous_id=self.owner.id,next_id=heir.id)
                    
            # Handle private objects
            if pri:
                perm = 'view_' + model_ref._meta.model_name
                # Below I have to loop over each object individually because of the way assign_perm is coded.
                # If the given obj is a list, the it calls bulk_assign_perms that checks for any permission (including through a group) using ObjectPermissionChecker.
                # As a result, if a user already has access through a group explicit permission (user-object pair) is not created.
                for obj in pri:
                    assign_perm(perm,heir,obj) # assign view permission to the new owner for the private lenses

                if object_type != 'SledGroup':
                    # Notify users with access (except the previous owner, who has access already)
                    users_with_access,accessible_objects = heir.accessible_per_other(pri,'users')
                    for i,user in enumerate(users_with_access):
                        if user.id != self.owner.id:
                            objects = []
                            for j in accessible_objects[i]:
                                objects.append(pri[j])
                            ad_col = AdminCollection.objects.create(item_type=object_type,myitems=objects)
                            notify.send(sender=self.owner,
                                        recipient=user,
                                        verb='CedeOwnershipNote',
                                        level='info',
                                        timestamp=timezone.now(),
                                        action_object=ad_col,
                                        previous_id=self.owner.id,
                                        next_id=heir.id)
                        
                    # Notify groups with access
                    groups_with_access,accessible_objects = heir.accessible_per_other(pri,'groups')
                    id_list = [g.id for g in groups_with_access]
                    gwa = SledGroup.objects.filter(id__in=id_list) # Needed to cast Group to SledGroup
                    for i,group in enumerate(groups_with_access):
                        objects = []
                        for j in accessible_objects[i]:
                            objects.append(pri[j])
                        ad_col = AdminCollection.objects.create(item_type=object_type,myitems=objects)
                        action.send(self.owner,target=gwa[i],verb='CedeOwnershipGroup',level='info',action_object=ad_col,previous_id=self.owner.id,next_id=heir.id)
                
            # Confirm to the previous owner
            notify.send(sender=heir,
                        recipient=self.owner,
                        verb='CedeOwnershipAcceptedNote',
                        level='success',
                        timestamp=timezone.now(),
                        action_object=self)

        else:
            notify.send(sender=heir,
                        recipient=self.owner,
                        verb='CedeOwnershipRejectedNote',
                        level='error',
                        timestamp=timezone.now(),
                        action_object=self)
'''
