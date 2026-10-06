from django.db import models

from gerlumph_maps.models import MagMaps
from gerlumph_users.models import Users



class Downloads(models.Model):
    owner = models.ForeignKey(Users,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,help_text="The date and time when the download was requested.")
    maps = models.ManyToManyField(MagMaps)


    class Meta():
        db_table = "downloads"
        verbose_name = "download"
        verbose_name_plural = "downloads"
        ordering = ["-created_at"]

        
    def __str__(self):
        date_string = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return '%s %s' % (self.owner.username,date_string)

    def get_absolute_url(self):
        return reverse('gerlumph_downloads:download-detail',kwargs={'pk':self.id})
