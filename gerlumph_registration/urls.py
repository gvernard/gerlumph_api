from django.urls import path, re_path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


app_name = 'gerlumph_registration'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.myLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='gerlumph_registration/login.html'), name='logout'),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name="password/password_reset_confirm.html",
             success_url=reverse_lazy(app_name+':password_reset_complete') 
         ),
         name='password_reset_confirm'
         ),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'), name='password_reset_complete'),
]
