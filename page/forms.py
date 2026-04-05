
from django import forms
from .models import FundingRequest, Gender, LossAlert, MessageContact, Donation, UserDetails, FundPayment, Comment, Region, Prefecture, Commune, Quarter
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import os


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
    max_upload_size = 1 * 1024 * 1024  # 1 MB
    def to_python(self, data):
        if not data:
            return []
        return data

    def validate(self, data):
        # Call the parent class's validate method
        super().validate(data)
        for file in data:
            # Truncate long filenames but preserve extension
            if len(file.name) > 50:
                base, ext = os.path.splitext(file.name)
                base_max = max(1, 50 - len(ext))
                file.name = f"{base[:base_max]}{ext}"

            if file.size > self.max_upload_size:
                raise forms.ValidationError(
                    _('La taille du fichier doit être inférieure à %(max_size)s. Taille actuelle: %(current_size)s.') % {
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
            'beneficiary_name','funding_request_type', 'funding_amount','title','description_needs',
            'region','prefecture','commune','quarter', 'address', 'email', 'phone', 'start_date','end_date',  'principal_image'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['prefecture'].queryset = Prefecture.objects.none()
        self.fields['commune'].queryset = Commune.objects.none()
        self.fields['quarter'].queryset = Quarter.objects.none()

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=region_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'prefecture' in self.data:
            try:
                prefecture_id = int(self.data.get('prefecture'))
                self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=prefecture_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'commune' in self.data:
            try:
                commune_id = int(self.data.get('commune'))
                self.fields['quarter'].queryset = Quarter.objects.filter(commune_id=commune_id).order_by('name')
            except (ValueError, TypeError):
                pass

        # For editing instances
        if self.instance and self.instance.pk:
            if self.instance.region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region=self.instance.region).order_by('name')
            if self.instance.prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture=self.instance.prefecture).order_by('name')
            if self.instance.commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune=self.instance.commune).order_by('name')
    
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
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea col s12 m12'}), label="Description")
    optional_docs = MultipleFileField(required=False)
    class Meta:
        model = LossAlert
        fields = ['name', 'loss_alert_type', 'description',  'email', 'phone', 'region','prefecture','commune','quarter', 'address', 'date_alert', 'hour_alert','principal_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['prefecture'].queryset = Prefecture.objects.none()
        self.fields['commune'].queryset = Commune.objects.none()
        self.fields['quarter'].queryset = Quarter.objects.none()

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=region_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'prefecture' in self.data:
            try:
                prefecture_id = int(self.data.get('prefecture'))
                self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=prefecture_id).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'commune' in self.data:
            try:
                commune_id = int(self.data.get('commune'))
                self.fields['quarter'].queryset = Quarter.objects.filter(commune_id=commune_id).order_by('name')
            except (ValueError, TypeError):
                pass

        # For editing instances
        if self.instance and self.instance.pk:
            if self.instance.region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region=self.instance.region).order_by('name')
            if self.instance.prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture=self.instance.prefecture).order_by('name')
            if self.instance.commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune=self.instance.commune).order_by('name')

class MessageContactForm(forms.ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre nom.'}, label="Nom")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre email.'}, label="Email")
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class': 'materialize-textarea', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre message.'}, label="Message")
    class Meta:
        model = MessageContact
        fields = ['name', 'email', 'message']
        
        

class DonationForm(forms.ModelForm):
    donor_first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre prénom.'}, label="Prénom du donateur")
    donor_last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre nom.'}, label="Nom du donateur")
    donor_phone = forms.CharField(widget=forms.TextInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre numéro de téléphone.'}, label="Téléphone du donateur")
    donor_email = forms.EmailField(widget=forms.EmailInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre email.'}, label="Email du donateur")
    donor_address = forms.CharField(widget=forms.TextInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre adresse.'}, label="Adresse du donateur")
    donor_city = forms.CharField(widget=forms.TextInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre ville.'}, label="Ville du donateur")
    #Country field should be a dropdown list with countries from userdetails countries model
    amount = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate col s12 col m12', 'required': 'required', 'type': 'number', 'min': '10000', 'step': '1000'}), error_messages={'required': 'Veuillez renseigner votre montant.', 'min': 'Le montant doit au moins atteindre 10000 GNF'}, label="Montant (En GNF) à donner")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10,'class':'materialize-textarea col s12 col m12'}), label="Description", required=False)

    class Meta:
        model = Donation
        fields = ['amount', 'donor_first_name', 'donor_last_name',  'donor_country','donor_city','donor_phone', 'donor_email', 'donor_address', 'description']

class FundingPaymentForm(forms.ModelForm):
    amount = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required', 'type': 'number', 'min': '10000', 'step': '1'}),
        error_messages={'required': 'Veuillez renseigner votre montant.', 'min': 'Le montant doit au moins atteindre 10000 GNF'},
        label="Montant (En GNF) à financer"
    )
    donor_first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre prénom.'},
        label="Prénom du donateur"
    )
    donor_last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre nom.'},
        label="Nom du donateur"
    )
    donor_phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre numéro de téléphone.'},
        label="Téléphone du donateur"
    )
    donor_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'validate', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre email.'},
        label="Email du donateur"
    )
    donor_address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre adresse.'},
        label="Adresse du donateur"
    )
    donor_city = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'validate col s12 col m6', 'required': 'required'}),
        error_messages={'required': 'Veuillez renseigner votre ville.'},
        label="Ville du donateur"
    )

    class Meta:
        model = FundPayment
        fields = ['amount', 'donor_first_name', 'donor_last_name','donor_country','donor_city', 'donor_phone', 'donor_email', 'donor_address',  ]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "Ajoutez un commentaire...",
                'class': 'materialize-textarea'
            })
        }
        labels = {
            'text': ''
        }
