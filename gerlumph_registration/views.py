from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import LoginView
from django.contrib.sites.models import Site
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.template.response import TemplateResponse

from .forms import RegisterForm, UserLoginForm

from gerlumph_users.models import Users #, ConfirmationTask
import smtplib


class myLoginView(LoginView):
    template_name = "gerlumph_registration/login.html"
    authentication_form = UserLoginForm
    
    def form_valid(self,form):
        username = self.request.POST["username"]
        password = self.request.POST["password"]
        user = authenticate(self.request,username=username,password=password)
        if user is not None:
            login(self.request,user)
            return HttpResponseRedirect(self.get_success_url())
        else:
            message = 'Authentication error - Please contact the administrators.'
            messages.add_message(self.request,messages.ERROR,message)
            return HttpResponseRedirect(self.request.path_info)
        


# Create your views here.
def register(response):
    #if someone is posting their form data, redirect them to (home for now)
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            candidate_user = form.save(commit=False)
            candidate_user.is_active = False
            candidate_user.save()

            #create a confirmation task for a random admin
            cargo = {}
            cargo['object_type'] = 'Users'
            cargo['object_ids'] = [candidate_user.id]
            #cargo['user_admin'] = Users.selectRandomAdmin()[0].username
            #ConfirmationTask.create_task(candidate_user,Users.getAdmin(),'AcceptNewUser',cargo)
            message = "The admins have been notified and will soon process your registration!"
            #messages.add_message(response,messages.SUCCESS,message)
            #return HttpResponseRedirect("../login/")
            return TemplateResponse(response,'simple_message.html',context={'message':message})
    else:
        form = RegisterForm()

    return render(response, "gerlumph_registration/register.html", {"form":form}) 


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = Users.objects.filter(Q(email=data))
            if associated_users.exists():

                user = associated_users.first()
                subject = 'GERLUMPH: Password reset'
                html_message = get_template('emails/password_reset.html')
                domain = Site.objects.get_current().domain
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                mycontext = {
                    'first_name': user.first_name,
                    'protocol': request.scheme,
                    'domain': domain, #site.domain, THIS HAS TO BE SET MANUALLY...
                    'uid': uid,
                    'token': token,
                }
                html_message = html_message.render(mycontext)
                plain_message = strip_tags(html_message)
                
                user_email = user.email
                from_email = 'gerlumph-no-reply@gerlumph.amnh.org'
                send_mail(subject,plain_message,from_email,[user_email],html_message=html_message)
                link = request.scheme+'://'+domain+reverse('gerlumph_registration:password_reset_confirm',args=[uid,token])
                #print(link)
                
                return redirect ("gerlumph_registration:password_reset_done")
            else:
                password_reset_form.add_error(None,"This email address does not correspond to an existing user.")
                return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})

