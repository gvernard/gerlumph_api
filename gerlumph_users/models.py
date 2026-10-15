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

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
import base64
from django.db.models.functions import ExtractWeek, ExtractIsoWeekDay
matplotlib.use('Agg')  # Prevents headless server GUI errors



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



    def get_contribution_plot(self,qset_downloads=None):
        # 1. Generate 52 weeks of dummy data (7 days a week)
        #np.random.seed(42)
        #grid = np.random.choice([0, 1, 2, 4, 8], size=(7, 52), p=[0.5, 0.2, 0.15, 0.1, 0.05])

        if qset_downloads == None:
            from gerlumph_downloads.models import Downloads
            qset_downloads = Downloads.objects.filter( Q(owner=self) ).order_by('-created_at')

        
        qset = qset_downloads.annotate(
            week=ExtractWeek("created_at"), weekday=ExtractIsoWeekDay("created_at")
        ).values("week", "weekday").annotate(count=Count("maps")).order_by('week','weekday')
        
        unique_weeks = sorted(list(set(entry["week"] for entry in qset)))
        #week_to_idx = {week: idx for idx, week in enumerate(unique_weeks)}
        grid = np.array( [[0 for _ in range(52)] for _ in range(7)] )
        
        for entry in qset:
            #w_idx = week_to_idx[entry["week"]]
            w_idx = entry["week"]
            d_idx = entry["weekday"] - 1
            grid[d_idx][w_idx] = entry["count"]
                
                
        n_colors = np.max(grid) + 1
        cmap = matplotlib.colormaps['Purples']
        colors = cmap(np.linspace(0, 1, n_colors))
        colors = [ matplotlib.colors.to_hex(color) for color in colors ]
        
        #print(grid.shape)
        #print(n_colors)
        #print(grid)
        
        
        plt.figure(figsize=(12, 2))
        ax = sns.heatmap(
            grid,
            cmap=colors,
            cbar=False,
            linewidths=2,
            linecolor='white',
            square=True
        )
        
        ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], rotation=0)
        #ax.set_xticklabels([]) # Hide week numbers
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = string.decode('utf-8')
        
        return uri
    

        
    

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
