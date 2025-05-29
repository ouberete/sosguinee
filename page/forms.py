
from django import forms
from .models import FundingRequest, Gender, LossAlert, MessageContact, Donation
from django.contrib.auth.models import User


class CustomClearableFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs['multiple'] = 'multiple'
        self.attrs = attrs

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)
    
def filesizeformat(value):
    """
    Formats the value (which is assumed to be in bytes) as a human-readable file size.
    """
    if value < 1024:
        return f"{value} bytes"
    elif value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    elif value < 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    else:
        return f"{value / (1024 * 1024 * 1024):.1f} GB"

class MultipleFileField(forms.FileField):
    widget = CustomClearableFileInput
    max_upload_size = 5 * 1024 * 1024  # 5 MB
    def to_python(self, data):
        if not data:
            return []
        return data

    def validate(self, data):
        # Call the parent class's validate method
        super().validate(data)
        for file in data:
           
            #Check if the file name is not too large then rename with short name
            if len(file.name) > 50:
                file.name = file.name[:50]
                
            if file.size > self.max_upload_size:
                raise forms.ValidationError(
                    _('la taille du fichier doit faire moins de %(max_size)s. Taille actuelle %(current_size)s.') % {
                        'max_size': filesizeformat(self.max_upload_size),
                        'current_size': filesizeformat(file.size)
                    }
                )

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)
    




class FundingRequestForm(forms.ModelForm):
    description_needs = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'materialize-textarea'}),
        max_length=255,
        help_text='Max. 255 characters',
        label="Description des besoins",
        initial="",
        strip=True
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Date de debut")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Date de fin")
    optional_docs = MultipleFileField(required=False)

    class Meta:
        model = FundingRequest
        fields = [
            'beneficiary_name', 'description_needs', 'country', 'city',
            'quarter', 'address', 'funding_request_type',
            'funding_amount', 'email', 'phone', 'start_date','end_date', 'title', 'principal_image'
        ] 
    
    #throw errors if start date is greater than end date
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                self.add_error('start_date', 'La date de fin doit être superieur a la date de debut')
                self.add_error('end_date', 'La date de fin doit être superieur a la date de debut')
                
                
                
class LossAlertForm(forms.ModelForm):
    hour_alert = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False, label="Heure d'alerte")
    date_alert = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Date d'alerte")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea'}), label="Description")
    optional_docs = MultipleFileField()
    class Meta:
        model = LossAlert
        fields = ['name', 'loss_alert_type', 'description',  'email', 'phone', 'country', 'city', 'quarter', 'address', 'date_alert', 'hour_alert','principal_image','optional_docs']

class MessageContactForm(forms.ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre nom.'}, label="Nom")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre email.'}, label="Email")
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre message.'}, label="Message")
    class Meta:
        model = MessageContact
        fields = ['name', 'email', 'message']
        
        
        
class DonationForm(forms.ModelForm):
    amount = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre montant.'}, label="Montant")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea'}), label="Description", required=False)

    class Meta:
        model = Donation
        fields = ['amount', 'description']

