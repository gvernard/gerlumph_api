from django.urls import path
from . import views

app_name = 'gerlumph_limits'
urlpatterns = [
    path('limits-and-roles/<int:pk>',views.LimitsAndRolesUpdateView.as_view(),name='limits-and-roles-update'),
]
