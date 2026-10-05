from django import forms
from bootstrap_modal_forms.forms import BSModalForm
#from mysite.language_check import validate_language


class CedeOwnershipForm(BSModalForm):
    mychoices = [('yes','Yes'),('no','No')]
    response = forms.ChoiceField(label='Response',
                                 widget=forms.RadioSelect(attrs={'class':'jb-select-radio'}),
                                 choices=mychoices
                                 )
    response_comment = forms.CharField(label='',
                                       widget=forms.Textarea(attrs={'placeholder': 'Say something back','rows':3,}),
                                       #validators=[validate_language]
                                       )

    
class DeleteObjectForm(BSModalForm):
    mychoices = [('yes','Yes'),('no','No')]
    response = forms.ChoiceField(label='Response',
                                 widget=forms.RadioSelect(attrs={'class':'jb-select-radio'}),
                                 choices=mychoices
                                 )
    response_comment = forms.CharField(label='',
                                       widget=forms.Textarea(attrs={'placeholder': 'Say something back','rows':3,}),
                                       #validators=[validate_language]
                                       )

    
class AcceptNewUserForm(BSModalForm):
    mychoices = [('yes','Yes'),('no','No')]
    response = forms.ChoiceField(label='Response',
                                 widget=forms.RadioSelect(attrs={'class':'jb-select-radio'}),
                                 choices=mychoices
                                 )
    response_comment = forms.CharField(label='',
                                       widget=forms.Textarea(attrs={'placeholder': 'Say something back','rows':3,}),
                                       #validators=[validate_language]
                                       )
