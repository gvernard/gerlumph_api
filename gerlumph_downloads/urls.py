from django.urls import path
from . import views

app_name = 'gerlumph_downloads'
urlpatterns = [
    path('detail/<int:pk>/',views.DownloadDetailView.as_view(),name='download-detail'),
    path('admin-download-list/',views.AdminDownloadList.as_view(),name='admin-download-list'),
    path('admin-download-user/<int:other_user>',views.AdminDownloadUser.as_view(),name='admin-download-user'),
]
