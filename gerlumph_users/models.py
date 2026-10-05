from django.db import models
from django.db.models import Q, CharField, Count
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone
from django.apps import apps

from guardian.core import ObjectPermissionChecker
from guardian.mixins import GuardianUserMixin
#from guardian.shortcuts import assign_perm, remove_perm, get_objects_for_group, get_objects_for_user

#from operator import itemgetter
#from itertools import groupby
import inspect

#from . import SingleObject, ConfirmationTask

#from gerlumph_downloads.models import Downloads

objects_with_owner = ["MagMaps","ConfirmationTask"]


class Users(AbstractUser,GuardianUserMixin):
    """ The class to represent registered users within GERLUMPH.

    A GERLUMPH user can own objects with which they can interact, e.g. give access to other users, cede ownership, add/remove objects from owned collections, etc.
    
    Attributes:
        affiliation (`CharField`): Affiliation is the only field in addition to the standard django `User` fields.
    """
    email = models.EmailField(unique=True,
                              blank=False)
    affiliation = models.CharField(
        blank=False,
        max_length=100,
        help_text="An affiliation, e.g. an academic or research institution etc.")
    info = models.TextField(
        blank=False,
        default='',
        help_text="A short description of your work and interests.",
        #validators=[validate_language]
    )
    
    class Meta():
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["username"]
    
    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('gerlumph_users:user-visit-card',kwargs={'username':self.username})

    
    def getOwnedObjects(self,user_object_types=None):
        """
        Provides access to all the objects that the user owns, arranged by type.

        Args:
            user_object_types (optional[List[str]]): A list of strings matching the names of the primary model database tables.
            The list is filtered to keep only those provided names that indeed correspond to primary models.
            If `None` then all the primary models are used.

        Returns:
            dict: The keys are the same as the filtered input object_types, or the entire list of `objects_with_owner`.
            The values are `QuerySets` corresponding to a query in each primary model table with the owner_id set to this user.
        """
        if user_object_types == None:
            filtered_object_types = objects_with_owner
        else:
            filtered_object_types = [x for x in user_object_types if x in objects_with_owner]
        objects = {}
        for table in filtered_object_types:
            #model_ref = apps.get_model(app_label='lenses',model_name=table)
            #objects[table] = model_ref.accessible_objects.owned(self)
            objects[table] = []
        return objects

    
    
    def checkOwnsList(self,objects):
        """
        Finds any objects in the given list that are not owned by the user.

        Args:
            objects(List[SingleObject]): A list of primary objects of a specific type.

        Raises:
            AssertionError: If the provided list contains objects that the user does not own.
        """
        not_owned = []
        for obj in objects:
            if not obj.isOwner(self):
                not_owned.append(obj)
        try:
            assert (len(not_owned) == 0), "User "+self.username+" is NOT the owner of "+str(len(not_owned))+" objects in the list."
        except AssertionError as error:
            caller = inspect.getouterframes(inspect.currentframe(),2)
            print(error,"The operation of '"+caller[1][3]+"' should not proceed")
            raise

        
    def cedeOwnership(self,objects,heir,justification=None):
        """
        Changes the owner of the given objects to the heir.
        
        First makes sure that the user owns all the objects, then creates a confirmation task for the heir.

        Args:
            objects(List[SingleObject]): A list of primary objects of a specific type.
            heir (`Queryset`): A Queryset consisting of only one user

        Returns:
            task: A confirmation task
        """
        # If input argument is a single value, convert to list
        if isinstance(objects,SingleObject):
            objects = [objects]
        # Check that user is the owner
        self.checkOwnsList(objects)

        try:
            assert (heir[0].is_active == True), "User "+user.username+" is NOT active and therefore cannot become the new owner of the objects in the list."
        except AssertionError as error:
            print(error)
            caller = inspect.getouterframes(inspect.currentframe(),2)
            print("The operation of '"+caller[1][3]+"' should not proceed")
            raise
        
        cargo = {}
        cargo["object_type"] = objects[0]._meta.model.__name__
        ids = []
        for obj in objects:
            ids.append(obj.id)
        cargo["object_ids"] = ids
        cargo["comment"] = justification
        #mytask = ConfirmationTask.create_task(self,heir,'CedeOwnership',cargo)
        #return mytask
        return cargo
        

    def get_pending_tasks(self):
        # This is to facilitate calls in templates
        pending_tasks = list(ConfirmationTask.custom_manager.pending_for_user(self))
        return pending_tasks

    def get_roles(self):
        roles = []
        if self.limitsandroles.is_admin:
            roles.append('admin') 
        if self.limitsandroles.is_super_admin:
            roles.append('super admin') 
        if len(roles) > 0:
            return ','.join(roles)
        else:
            return ''


    

    ####################################################################
    # Below this point lets put actions relevant only to the admin users
    def getAdmin():
        return Users.objects.filter(is_superuser=True) # This refers to the django user 'admin'
    

    def selectRandomAdmin(exclude_usernames=None):
        # Returns a queryset
        if exclude_usernames is None:
            exclude_usernames = []
        user_id = Users.objects.filter(limitsandroles__is_admin=True).exclude(username__in=exclude_usernames).order_by('?').first().id
        qset = Users.objects.filter(id=user_id)
        return qset

      
    def get_admin_pending_tasks(self):
        if self.limitsandroles.is_admin:
            admin = Users.getAdmin()[0]
            pending_tasks = list(ConfirmationTask.objects.filter(status='P').filter(Q(owner=admin)|Q(recipients__username=admin.username)))
            return pending_tasks
        else:
            return []

        
    '''
    def check_all_limits(self,N,obj_type='all'):
        remaining = {
            "errors": []
        }
        #print(N,obj_type)
        N_remaining_day = self.check_limit_day(N,obj_type)
        if N_remaining_day < 0:
            remaining["errors"].append('You have exceeded the limit of daily downloads! Contact the admins.')
        else:
            remaining["N_remaining_day"] = N_remaining_day
        
        N_remaining_week = self.check_limit_week(N,obj_type)
        if N_remaining_week < 0:
            remaining["errors"].append('You have exceeded the limit of weekly downloads! Wait for a max. of 7 days, or contact the admins.')
        else:
            remaining["N_remaining_week"] = N_remaining_week

        return remaining
    
        
    def check_limit_day(self,N):
        downloads = Downloads.accessible_objects.owned(self)
        N_maps = 0
        for i,down in owned_objects.items():
            N_owned = N_owned + qset.count()
        remaining = self.limitsandroles.limit_total_owned - N_owned - N
        return remaining

        
    def check_limit_week(self,N,obj_type='all'):
        owned_objects = self.getOwnedObjects()
        N_week = 0
        last_seven_days = timezone.now() - timezone.timedelta(days=7)
        for model_type,qset in owned_objects.items():
            N_week = N_week + qset.filter(created_at__gt=last_seven_days).count()
        remaining = self.limitsandroles.limit_add_per_week - N_week - N
        return remaining
    '''

