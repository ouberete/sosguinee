
from django import forms
from .models import FundingRequest, Gender, UserDetails, LossAlert
from django.contrib.auth.models import User


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result
    
class FundingRequestForm(forms.ModelForm):
    description_needs = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'class': 'materialize-textarea'}), max_length=255, help_text='Max. 255 characters', label="What needs to be done?", initial="", strip=True)
    optional_images = forms.FileField(widget=MultipleFileField())
    class Meta:
        model = FundingRequest
        fields = ['beneficiary_name', 'description_needs','country', 'city','quarter','address', 'funding_request_type','funding_request_status', 'funding_amount', 'email', 'phone', 'principal_image']
 
class LossAlertForm(forms.ModelForm):
    hour_alert = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    date_alert = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea'}))
    class Meta:
        model = LossAlert
        fields = ['name', 'loss_alert_type', 'loss_alert_status', 'description', 'principal_image', 'email', 'phone', 'country', 'city', 'quarter', 'address', 'date_alert', 'hour_alert']

