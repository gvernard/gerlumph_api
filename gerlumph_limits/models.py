from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Q, Count

from gerlumph_users.models import Users
from gerlumph_downloads.models import Downloads


class LimitsAndRoles(models.Model):
    user = models.OneToOneField(Users,on_delete=models.CASCADE,primary_key=True)

    ### Limits
    limit_down_per_week = models.IntegerField(blank=False,
                                              default=1000,
                                              verbose_name="Per week",
                                              help_text="The total number of maps downloaded in a week.",
                                              validators=[MinValueValidator(0,"This limit cannot be negative"),
                                                          MaxValueValidator(10000,"Wow, that's a lot of maps to be downloaded in a week, are you sure?")])
    limit_down_per_day = models.IntegerField(blank=False,
                                             default=100,
                                             verbose_name="Per day",
                                             help_text="The total number of maps downloaded in a day.",
                                             validators=[MinValueValidator(0,"This limit cannot be negative"),
                                                         MaxValueValidator(10000,"Wow, that's a lot of maps to be downloaded in a day, are you sure?")])

    ### Roles
    is_admin = models.BooleanField(blank=False,
                                   default=False,
                                   verbose_name="Admin",
                                   help_text="User admin role.")
    is_super_admin = models.BooleanField(blank=False,
                                         default=False,
                                         verbose_name="SUPER admin",
                                         help_text="User SUPER admin role (can assign admins).")
    

    class Meta():
        db_table = "limits_and_roles"

    def __str__(self):
        return self.user.username + ' limit and role'

    
    def check_limit_day(self,N):
        time_threshold = timezone.now() - timezone.timedelta(hours=24)
        downloads = Downloads.objects.filter( Q(owner=self.user), created_at__gte=time_threshold).aggregate(N_maps=Count('maps'))
        remaining = self.limit_down_per_day - downloads["N_maps"] - N
        return remaining

        
    def check_limit_week(self,N):
        time_threshold = timezone.now() - timezone.timedelta(days=7)
        downloads = Downloads.objects.filter( Q(owner=self.user), created_at__gte=time_threshold).aggregate(N_maps=Count('maps'))
        remaining = self.limit_down_per_week - downloads["N_maps"] - N
        return remaining

    def check_all_limits(self,N):
        remaining = {
            "errors": []
        }
        #print(N,obj_type)
        N_remaining_day = self.check_limit_day(N)
        if N_remaining_day < 0:
            remaining["errors"].append('You have exceeded the limit of daily downloads! Contact the admins.')
        else:
            remaining["N_remaining_day"] = N_remaining_day
        
        N_remaining_week = self.check_limit_week(N)
        if N_remaining_week < 0:
            remaining["errors"].append('You have exceeded the limit of weekly downloads! Wait for a max. of 7 days, or contact the admins.')
        else:
            remaining["N_remaining_week"] = N_remaining_week

        return remaining
