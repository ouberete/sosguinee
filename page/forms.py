
from django import forms
from .models import FundingRequest, Gender, LossAlert, MessageContact, Donation, UserDetails, FundPayment, Comment, Region, Prefecture, Commune, Quarter
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image, ImageOps
import os

ALLOWED_OPTIONAL_DOC_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".avif",
    ".pdf",
}
ALLOWED_PRINCIPAL_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".avif",
}
IMAGE_FORMAT_BY_EXTENSION = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".avif": "AVIF",
}


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


def _normalize_image_extension(name, fallback_extension=".jpg"):
    base, ext = os.path.splitext(name or "")
    return f"{base}{ext or fallback_extension}"


def _compress_uploaded_image(uploaded_file, quality=82):
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)

    output = BytesIO()
    source_format = (image.format or os.path.splitext(uploaded_file.name)[1].lstrip(".")).upper()
    if source_format in {"JPG", "JPEG"}:
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
        target_name = _normalize_image_extension(uploaded_file.name, ".jpg")
    elif source_format == "PNG":
        image.save(output, format="PNG", optimize=True, compress_level=6)
        target_name = _normalize_image_extension(uploaded_file.name, ".png")
    elif source_format == "WEBP":
        image.save(output, format="WEBP", quality=quality, method=6)
        target_name = _normalize_image_extension(uploaded_file.name, ".webp")
    else:
        return uploaded_file

    uploaded_file.close()
    return ContentFile(output.getvalue(), name=target_name)

class MultipleFileField(forms.FileField):
    widget = CustomClearableFileInput
    max_upload_size = 1 * 1024 * 1024  # 1 MB
    max_file_count = 5

    def to_python(self, data):
        if not data:
            return []
        return data

    def validate(self, data):
        # Call the parent class's validate method
        super().validate(data)
        if len(data) > self.max_file_count:
            raise forms.ValidationError(
                _(
                    "Vous pouvez ajouter au maximum %(max_files)s documents."
                ) % {"max_files": self.max_file_count}
            )
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

            extension = os.path.splitext(file.name)[1].lower()
            if extension not in ALLOWED_OPTIONAL_DOC_EXTENSIONS:
                raise forms.ValidationError(
                    _(
                        "Type de fichier non autorisé (%(extension)s). "
                        "Formats autorisés: %(allowed)s."
                    ) % {
                        "extension": extension or "sans extension",
                        "allowed": ", ".join(sorted(ALLOWED_OPTIONAL_DOC_EXTENSIONS)),
                    }
                )

            file.seek(0)
            try:
                if extension == ".pdf":
                    valid_content = file.read(5) == b"%PDF-"
                else:
                    with Image.open(file) as image:
                        valid_content = image.format == IMAGE_FORMAT_BY_EXTENSION[extension]
                        image.verify()
            except Exception:
                valid_content = False
            finally:
                file.seek(0)

            if not valid_content:
                raise forms.ValidationError(
                    "Le contenu du fichier ne correspond pas au format annoncé."
                )

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)
    




class FundingRequestForm(forms.ModelForm):
    description_needs = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'materialize-textarea compact-textarea'}),
        max_length=255,
        help_text='Max. 255 characters',
        label="Description des besoins",
        initial="",
        strip=True
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Date de debut")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Date de fin")
    optional_docs = MultipleFileField(required=False)
    compress_principal_image = forms.BooleanField(
        required=False,
        initial=False,
        label="Compresser l'image principale",
        help_text="Optionnel: réduire le poids du fichier avant sauvegarde.",
        widget=forms.CheckboxInput(attrs={'class': 'filled-in'})
    )

    class Meta:
        model = FundingRequest
        fields = [
            'beneficiary_name', 'funding_request_type', 'funding_amount', 'title', 'description_needs',
            'region', 'prefecture', 'commune', 'quarter', 'address', 'email', 'phone', 'start_date', 'end_date', 'principal_image'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['prefecture'].queryset = Prefecture.objects.none()
        self.fields['commune'].queryset = Commune.objects.none()
        self.fields['quarter'].queryset = Quarter.objects.none()
        self.fields['principal_image'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.webp,.avif',
            'class': 'upload-input upload-input-image',
            'data-upload-input': 'principal_image',
        })
        self.fields['optional_docs'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.webp,.avif,.pdf',
            'class': 'upload-input upload-input-docs',
            'data-upload-input': 'optional_docs',
        })

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

        if self.instance and self.instance.pk:
            if self.instance.region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region=self.instance.region).order_by('name')
            if self.instance.prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture=self.instance.prefecture).order_by('name')
            if self.instance.commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune=self.instance.commune).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            self.add_error('start_date', 'La date de fin doit être superieur a la date de debut')
            self.add_error('end_date', 'La date de fin doit être superieur a la date de debut')
        return cleaned_data

    def clean_principal_image(self):
        principal_image = self.cleaned_data.get('principal_image')
        if not principal_image:
            return principal_image

        extension = os.path.splitext(principal_image.name)[1].lower()
        if extension not in ALLOWED_PRINCIPAL_IMAGE_EXTENSIONS:
            raise forms.ValidationError(
                _(
                    "Image principale non autorisée (%(extension)s). "
                    "Formats autorisés: %(allowed)s."
                ) % {
                    'extension': extension or 'sans extension',
                    'allowed': ', '.join(sorted(ALLOWED_PRINCIPAL_IMAGE_EXTENSIONS)),
                }
            )

        try:
            principal_image.seek(0)
            Image.open(principal_image).verify()
        except Exception:
            raise forms.ValidationError("Le fichier image principal semble corrompu ou invalide.")
        finally:
            try:
                principal_image.seek(0)
            except Exception:
                pass

        if self.cleaned_data.get('compress_principal_image'):
            principal_image = _compress_uploaded_image(principal_image)

        max_image_size = 3 * 1024 * 1024
        if principal_image.size > max_image_size:
            raise forms.ValidationError(
                _(
                    "L'image principale doit être inférieure à %(max_size)s. "
                    "Taille actuelle: %(current_size)s."
                ) % {
                    'max_size': filesizeformat(max_image_size),
                    'current_size': filesizeformat(principal_image.size),
                }
            )

        return principal_image


class LossAlertForm(forms.ModelForm):
    hour_alert = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False, label="Heure d'alerte")
    date_alert = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Date d'alerte")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'class': 'materialize-textarea compact-textarea col s12 m12'}), label="Description")
    optional_docs = MultipleFileField(required=False)
    compress_principal_image = forms.BooleanField(
        required=False,
        initial=False,
        label="Compresser l'image principale",
        help_text="Optionnel: réduire le poids du fichier avant sauvegarde.",
        widget=forms.CheckboxInput(attrs={'class': 'filled-in'})
    )

    class Meta:
        model = LossAlert
        fields = ['name', 'loss_alert_type', 'description', 'email', 'phone', 'region', 'prefecture', 'commune', 'quarter', 'address', 'date_alert', 'hour_alert', 'principal_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['prefecture'].queryset = Prefecture.objects.none()
        self.fields['commune'].queryset = Commune.objects.none()
        self.fields['quarter'].queryset = Quarter.objects.none()
        self.fields['principal_image'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.webp,.avif',
            'class': 'upload-input upload-input-image',
            'data-upload-input': 'principal_image',
        })
        self.fields['optional_docs'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.webp,.avif,.pdf',
            'class': 'upload-input upload-input-docs',
            'data-upload-input': 'optional_docs',
        })

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

        if self.instance and self.instance.pk:
            if self.instance.region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region=self.instance.region).order_by('name')
            if self.instance.prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture=self.instance.prefecture).order_by('name')
            if self.instance.commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune=self.instance.commune).order_by('name')

    def clean_principal_image(self):
        principal_image = self.cleaned_data.get('principal_image')
        if not principal_image:
            return principal_image

        extension = os.path.splitext(principal_image.name)[1].lower()
        if extension not in ALLOWED_PRINCIPAL_IMAGE_EXTENSIONS:
            raise forms.ValidationError(
                _(
                    "Image principale non autorisée (%(extension)s). "
                    "Formats autorisés: %(allowed)s."
                ) % {
                    'extension': extension or 'sans extension',
                    'allowed': ', '.join(sorted(ALLOWED_PRINCIPAL_IMAGE_EXTENSIONS)),
                }
            )

        try:
            principal_image.seek(0)
            Image.open(principal_image).verify()
        except Exception:
            raise forms.ValidationError("Le fichier image principal semble corrompu ou invalide.")
        finally:
            try:
                principal_image.seek(0)
            except Exception:
                pass

        if self.cleaned_data.get('compress_principal_image'):
            principal_image = _compress_uploaded_image(principal_image)

        max_image_size = 3 * 1024 * 1024
        if principal_image.size > max_image_size:
            raise forms.ValidationError(
                _(
                    "L'image principale doit être inférieure à %(max_size)s. "
                    "Taille actuelle: %(current_size)s."
                ) % {
                    'max_size': filesizeformat(max_image_size),
                    'current_size': filesizeformat(principal_image.size),
                }
            )

        return principal_image


class MessageContactForm(forms.ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': _('Veuillez renseigner votre nom.')}, label=_("Nom"))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'validate', 'required': 'required'}), error_messages={'required': _('Veuillez renseigner votre email.')}, label=_("Email"))
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 2,'class': 'materialize-textarea compact-textarea', 'required': 'required'}), error_messages={'required': _('Veuillez renseigner votre message.')}, label=_("Message"))
    class Meta:
        model = MessageContact
        fields = ['name', 'email', 'message']
        
        

# Champs d'identité rendus optionnels côté serveur : requis seulement si le
# paiement n'est PAS anonyme (validé dans clean()).
ANONYMIZABLE_IDENTITY_FIELDS = {
    'donor_first_name': 'Veuillez renseigner votre prénom.',
    'donor_last_name': 'Veuillez renseigner votre nom.',
    'donor_address': 'Veuillez renseigner votre adresse.',
    'donor_city': 'Veuillez renseigner votre ville.',
}


class _AnonymizablePaymentForm(forms.ModelForm):
    """Valide les champs d'identité uniquement si le paiement n'est pas anonyme."""

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount != amount.to_integral_value():
            raise forms.ValidationError("Le montant doit être un nombre entier de GNF.")
        return amount

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('is_anonymous'):
            for field_name, message in ANONYMIZABLE_IDENTITY_FIELDS.items():
                if field_name in self.fields and not (cleaned.get(field_name) or '').strip():
                    self.add_error(field_name, message)
        return cleaned


class DonationForm(_AnonymizablePaymentForm):
    donor_first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'validate'}), label="Prénom du donateur")
    donor_last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'validate'}), label="Nom du donateur")
    donor_phone = forms.CharField(widget=forms.TextInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre numéro de téléphone.'}, label="Téléphone du donateur")
    donor_email = forms.EmailField(widget=forms.EmailInput(attrs={'class':  'validate', 'required': 'required'}), error_messages={'required': 'Veuillez renseigner votre email.'}, label="Email du donateur")
    donor_address = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':  'validate'}), label="Adresse du donateur")
    donor_city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':  'validate'}), label="Ville du donateur")
    amount = forms.DecimalField(max_digits=18, decimal_places=0, min_value=10000, widget=forms.NumberInput(attrs={'class': 'validate', 'required': 'required', 'min': '10000', 'step': '1000'}), error_messages={'required': 'Veuillez renseigner votre montant.', 'min_value': 'Le montant doit au moins atteindre 10000 GNF'}, label="Montant (En GNF) à donner")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'materialize-textarea'}), label="Description", required=False)
    is_anonymous = forms.BooleanField(required=False, label="Faire un don anonyme (nous ne demandons que l'email et le téléphone)")

    class Meta:
        model = Donation
        fields = ['amount', 'donor_first_name', 'donor_last_name',  'donor_country','donor_city','donor_phone', 'donor_email', 'donor_address', 'description', 'is_anonymous']

class FundingPaymentForm(_AnonymizablePaymentForm):
    amount = forms.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=10000,
        widget=forms.NumberInput(attrs={'class': 'validate', 'required': 'required', 'min': '10000', 'step': '1'}),
        error_messages={'required': 'Veuillez renseigner votre montant.', 'min_value': 'Le montant doit au moins atteindre 10000 GNF'},
        label="Montant (En GNF) à financer"
    )
    donor_first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'validate'}),
        label="Prénom du donateur"
    )
    donor_last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'validate'}),
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
        required=False,
        widget=forms.TextInput(attrs={'class': 'validate'}),
        label="Adresse du donateur"
    )
    donor_city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'validate'}),
        label="Ville du donateur"
    )
    is_anonymous = forms.BooleanField(required=False, label="Faire un paiement anonyme (nous ne demandons que l'email et le téléphone)")

    class Meta:
        model = FundPayment
        fields = ['amount', 'donor_first_name', 'donor_last_name','donor_country','donor_city', 'donor_phone', 'donor_email', 'donor_address', 'is_anonymous']
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


