from django.urls import path
from . import views

app_name = 'gerlumph_maps'
urlpatterns = [
    path('detail/<int:pk>',views.MapDetailView.as_view(),name='map-detail'),
]
