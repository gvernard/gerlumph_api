from django.db import models

# Create your models here.
class MagMaps(models.Model):
    id = models.IntegerField(
        primary_key=True,
        blank=False,
        verbose_name="id",
        help_text="The GERLUMPH map id.",
        validators=[MinValueValidator(0,"This limit cannot be negative"),
                    MaxValueValidator(100000,"This is the upper limit of map ids.")])

    # kappa
    # gamma
    # s


    class Meta():
        db_table = "maps"
        verbose_name = "map"
        verbose_name_plural = "maps"
        ordering = ["-id"]
        
    def __str__(self):
        return self.id

    def get_absolute_url(self):
        return reverse('gerlumph_maps:map-detail',kwargs={'pk':self.id})


    def get_icon_url(self):
        icon = 'icon'
        return icon

    def get_sample_url(self):
        sample = 'sample'
        return sample

    def get_mpd_url(self):
        mpd = 'mpd'
        return mpd
