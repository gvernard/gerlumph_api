from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.storage import storages
from django.urls import reverse, reverse_lazy

my_storage = storages["s3bucket"]

# Create your models here.
class MagMaps(models.Model):
    id = models.IntegerField(
        primary_key=True,
        blank=False,
        verbose_name="id",
        help_text="The GERLUMPH map id.",
        validators=[MinValueValidator(0,"This limit cannot be negative"),
                    MaxValueValidator(100000,"This is the upper limit of map ids.")])

    kappa = models.DecimalField(blank=False,
                                max_digits=10,
                                decimal_places=5,
                                verbose_name="Kappa",
                                help_text="The convergence of the map.",
                                validators=[MinValueValidator(0.0,"Kappa must be positive."),
                                         MaxValueValidator(10.0,"Kappa must be less than 10.")])
    gamma = models.DecimalField(blank=False,
                                max_digits=10,
                                decimal_places=5,
                                verbose_name="Shear",
                                help_text="The shear of the map.",
                                validators=[MinValueValidator(0.0,"Shear must be positive."),
                                            MaxValueValidator(10.0,"Shear must be less than 10.")])
    s = models.DecimalField(blank=False,
                            max_digits=10,
                            decimal_places=5,
                            verbose_name="Smooth matter fraction",
                            help_text="The smooth matter fraction of the map.",
                            validators=[MinValueValidator(0,"Smooth matter fraction must be greater than or equal to zero."),
                                        MaxValueValidator(1,"Smooth matter fraction must be less than unity.")])

    res = models.IntegerField(blank=False,
                              verbose_name="Resolutiion",
                              help_text="The map resolution in pixels (assumes square maps).",
                              validators=[MinValueValidator(0,"Resolution must be greater than unity.")])
    width = models.DecimalField(blank=False,
                                max_digits=10,
                                decimal_places=5,
                                verbose_name="Width",
                                help_text="The width of the map in units of the Einstein radius (assumes square maps).",
                                validators=[MinValueValidator(0,"Width must be greater than unity.")],)
    
    mu_avg = models.DecimalField(blank=False,
                                 max_digits=10,
                                 decimal_places=5,
                                 verbose_name="Avg. magnification",
                                 help_text="The average magnification of the map.")
    N_avg = models.DecimalField(blank=False,
                                max_digits=10,
                                decimal_places=5,
                                verbose_name="Avg. number of rays",
                                help_text="The average number of rays per pixel.",
                                validators=[MinValueValidator(0,"Average number of rays must be greater than unity.")],)

    N_lenses = models.IntegerField(blank=False,
                                   verbose_name="Number of lenses",
                                   help_text="The number of lenses used to produce the map.",
                                   validators=[MinValueValidator(0,"Number of lenses must be greater than unity.")])
    t_tot = models.DecimalField(blank=False,
                                max_digits=10,
                                decimal_places=5,
                                verbose_name="Time",
                                help_text="The total time that was required to produce the map.",
                                validators=[MinValueValidator(0,"Time must be greater than zero.")],)

    
    class Meta():
        db_table = "maps"
        verbose_name = "map"
        verbose_name_plural = "maps"
        ordering = ["-id"]
        
    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('gerlumph_maps:map-detail',kwargs={'pk':self.id})

    def get_file_url(self,filename):
        # filename must contain the extension
        url = my_storage.url(str(self.id) + "/" + filename)
        return url

