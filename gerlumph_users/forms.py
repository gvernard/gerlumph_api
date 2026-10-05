import os
from django import forms
from bootstrap_modal_forms.forms import BSModalModelForm, BSModalForm
from gerlumph_users.models import Users
#from mysite.language_check import validate_no_profanity

class UsersSearchForm(forms.Form):
    search_term = forms.CharField(required=False,
                                  max_length=100,
                                  widget=forms.TextInput({'placeholder':'User name/surname/email keyword'}))
    mychoices = [
        ('any','any'),
        ('active','active'),
        ('inactive','inactive'),
        ('SuperAdmin','SuperAdmin'),
        ('Admin','Admin'),
        ('Inspector','Inspector'),
    ]
    role = forms.ChoiceField(label='Role',choices=mychoices) 
    page = forms.IntegerField(required=False,widget=forms.HiddenInput())



class UserUpdateForm(BSModalModelForm):

    class Meta:
        model = Users
        fields = ["first_name", "last_name", "email","affiliation", "info"]
        widgets = {
            "first_name": forms.TextInput({"placeholder":"your first name"}),
            "last_name": forms.TextInput({"placeholder":"your last name"}),
            "email": forms.TextInput({"placeholder":"your email"}),
            "affiliation": forms.TextInput({"placeholder":"your affiliation"}),
            "info": forms.Textarea({"placeholder":"your info"}),
        }

    def clean_first_name(self):
        data = self.cleaned_data["first_name"]
        #validate_no_profanity(data)
        return data

    def clean_last_name(self):
        data = self.cleaned_data["last_name"]
        #validate_no_profanity(data)
        return data

    def clean_info(self):
        data = self.cleaned_data["info"]
        #validate_no_profanity(data)
        return data

    def clean(self):
        # Check that at least one field was changed
        if not self.has_changed():
            self.add_error("__all__","No changes detected!")

            
        return
