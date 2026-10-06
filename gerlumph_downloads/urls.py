from django.urls import path
from . import views

app_name = 'gerlumph_downloads'
urlpatterns = [
    path('detail/<int:pk>/',views.DownloadDetailView.as_view(),name='download-detail'),
]
