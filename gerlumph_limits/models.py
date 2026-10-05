from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from gerlumph_users.models import Users


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

