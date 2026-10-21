from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from page.models import UserDetails, Region, Prefecture, Commune, Quarter
from django.utils.html import format_html
#from django.forms.widgets import RadioSelect
from django.forms.utils import flatatt
from django.contrib.auth import authenticate
from crispy_forms.helper import FormHelper
from PIL import Image
import os

from accounts.utils import send_or_queue_activation_email
User = get_user_model()

MAX_PRIVATE_UPLOAD_SIZE = 3 * 1024 * 1024
PRIVATE_IMAGE_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}
PRIVATE_DOCUMENT_EXTENSIONS = set(PRIVATE_IMAGE_FORMATS) | {".pdf"}


def _validate_private_upload(uploaded_file, allowed_extensions):
    if not uploaded_file:
        return uploaded_file

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in allowed_extensions:
        raise forms.ValidationError("Format de fichier non autorisé.")
    if uploaded_file.size > MAX_PRIVATE_UPLOAD_SIZE:
        raise forms.ValidationError("Le fichier ne doit pas dépasser 3 Mo.")

    uploaded_file.seek(0)
    try:
        if extension == ".pdf":
            valid_content = uploaded_file.read(5) == b"%PDF-"
        else:
            with Image.open(uploaded_file) as image:
                valid_content = image.format == PRIVATE_IMAGE_FORMATS[extension]
                image.verify()
    except Exception:
        valid_content = False
    finally:
        uploaded_file.seek(0)

    if not valid_content:
        raise forms.ValidationError("Le contenu du fichier ne correspond pas au format annoncé.")
    return uploaded_file


class PrivateDocumentValidationMixin:
    def clean_photo(self):
        return _validate_private_upload(self.cleaned_data.get("photo"), PRIVATE_IMAGE_FORMATS)

    def clean_id_card(self):
        return _validate_private_upload(self.cleaned_data.get("id_card"), PRIVATE_DOCUMENT_EXTENSIONS)

    def clean_birth_piece(self):
        return _validate_private_upload(self.cleaned_data.get("birth_piece"), PRIVATE_DOCUMENT_EXTENSIONS)

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Identifiant (Email ou nom d'utilisateur)",
        widget=forms.TextInput(attrs={
            'class': 'validate',
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'validate',
            'id': 'password-field'      # <- on fixe un id simple
        })
    )

    def clean(self):
        cleaned = super().clean()
        ident = (cleaned.get('username') or '').strip()
        pwd = cleaned.get('password')

        if ident and pwd:
            candidates = list(
                User.objects.filter(
                    Q(username__iexact=ident) | Q(email__iexact=ident)
                ).order_by('-is_active', '-last_login', '-date_joined')
            )

            if not candidates:
                raise forms.ValidationError("Identifiant ou Mot de passe incorrect.")

            # Si plusieurs utilisateurs correspondent (ex: même email sur plusieurs comptes),
            # on vérifie le mot de passe sur chacun pour identifier le bon compte.
            user_obj = None
            for candidate in candidates:
                if candidate.check_password(pwd):
                    user_obj = candidate
                    break

            if user_obj is None:
                raise forms.ValidationError("Identifiant ou Mot de passe incorrect.")

            profile = UserDetails.objects.filter(user=user_obj).order_by('-created_at').first()
            account_status = profile.user_status if profile and profile.user_status else (
                "Active" if user_obj.is_active else "Inactive"
            )

            if account_status == "Blocked":
                raise forms.ValidationError(
                    "Votre compte a ete bloque. Veuillez contacter l'administrateur."
                )

            if not user_obj.is_active:
                if account_status == "Active":
                    user_obj.is_active = True
                    user_obj.save(update_fields=["is_active"])
                else:
                    raise forms.ValidationError(
                        "Votre compte n'est pas encore actif. "
                        "Veuillez verifier votre email d'activation."
                    )

            user = authenticate(username=user_obj.username, password=pwd)
            if not user:
                user = user_obj
                user.backend = 'django.contrib.auth.backends.ModelBackend'
            cleaned['user'] = user

        return cleaned



class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'validate',
        }),
        error_messages={'required': "Veuillez renseigner votre prénom."}
    )
    last_name = forms.CharField(
        required=True,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'validate',
        }),
        error_messages={'required': "Veuillez renseigner votre nom."}
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'validate',
        }),
        error_messages={
            'required': "Veuillez renseigner votre email.",
            'invalid': "Format d'email invalide.",
        }
    )
    civility = forms.ChoiceField(
        choices=UserDetails.CIVILITY_CHOICES,
        label="Civilité",
        widget=forms.Select(attrs={'class': 'browser-default'}),
        error_messages={'required': "Veuillez sélectionner votre civilité."}
    )
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'validate',
            'id': 'password-field'      # <- on fixe un id simple
        })
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'validate',
            'id': 'password-field2'     # <- on fixe un id simple
        }),
        help_text="Entrez le même mot de passe que précédemment, pour vérification."
    )
    class Meta:
        model = User
        fields = ["civility", "first_name", "last_name", "username", "email", "password1", "password2"]
        widgets = {
            'username':   forms.TextInput(attrs={
                'class': 'validate'}),
        }
        error_messages = {
            'username': {
                'required': "Veuillez renseigner un nom d'utilisateur.",
                'min_length': "Au moins 3 caractères.",
                'unique': "Ce nom d'utilisateur existe déjà."
            }
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2
    
    def save(self, commit=True):
        # Crée un utilisateur inactif et son profil.
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
            UserDetails.objects.create(
                user=user,
                civility=self.cleaned_data["civility"],
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                user_status='Inactive'
            )
        self._send_activation_email(user)
        
        return user

    def _send_activation_email(self, user):
        # Let the view keep the user on the signup form when the email
        # backend fails; displaying account_created would be misleading.
        send_or_queue_activation_email(user, reuse_unsent=True)


class ResendActivationForm(forms.Form):
    identifier = forms.CharField(
        label="Email ou nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'validate',
        }),
    )


class _LegacyUserInfosForm(forms.ModelForm):
    user_category = forms.ChoiceField(choices=UserDetails.USER_CATEGORY_CHOICES, required=True, label="Catégorie d'utilisateur", error_messages={'required': 'Veuillez renseigner votre categorie d\'utilisateur.'}) 
    civility = forms.ChoiceField(choices=UserDetails.CIVILITY_CHOICES, label="Civilité", error_messages={'required': 'Veuillez renseigner votre civilité.'}, widget=forms.Select(attrs={'class': 'form-control; col-md-6'}))
    
    first_name = forms.CharField(max_length=100, label="Prénom", error_messages={'required': 'Veuillez renseigner votre prénom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", error_messages={'required': 'Veuillez renseigner votre Nom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(format="%Y-%m-%d",attrs={'type': 'date', 'class': 'form-control'}), label="Date de naissance", error_messages={'required': 'Veuillez renseigner votre date de naissance.'})
    birth_city = forms.CharField(max_length=100, label="Ville de naissance", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #birth_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,label="Pays de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    nationality = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Nationalité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    #is_actual_country_as_birth_country = forms.BooleanField(label="Definir le pays actuel et la ville", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    actual_city = forms.CharField(max_length=100, label="Ville actuelle", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #actual_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,required=False, label="Pays actuel", widget=forms.Select(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, label="Code postal", widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=100, label="Adresse actuelle", error_messages={'required': 'Veuillez renseigner votre adresse.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, label="Téléphone", error_messages={'required': 'Veuillez renseigner votre téléphone.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession_situation = forms.ChoiceField(label="Situation professionnelle", error_messages={'required': 'Veuillez renseigner votre situation professionnelle.'}, widget=forms.Select(attrs={'class': 'form-control'}), choices=UserDetails.PROFESSION_SITUATION_CHOICES)
    activity_sector = forms.ChoiceField(choices=UserDetails.ACTIVITY_SECTOR_CHOICES, label="Secteur d'activité", error_messages={'required': 'Veuillez renseigner votre secteur d\'activité.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    profession = forms.ChoiceField(choices=UserDetails.PROFESSION_CHOICES, label="Profession", error_messages={'required': 'Veuillez renseigner votre profession.'}, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
            model = UserDetails
            fields = ['user_category', 'civility','first_name','last_name', 'birth_date','birth_city', 'nationality', 'actual_city', 'zip_code', 'address', 'phone', 'profession_situation', 'activity_sector', 'profession', 'high_education', 'person_contact']

class _LegacyUserInfosFormWithLocations(forms.ModelForm):
    user_category = forms.ChoiceField(choices=UserDetails.USER_CATEGORY_CHOICES, required=True, label="Catégorie d'utilisateur", error_messages={'required': 'Veuillez renseigner votre categorie d\'utilisateur.'})
    civility = forms.ChoiceField(choices=UserDetails.CIVILITY_CHOICES, label="Civilité", error_messages={'required': 'Veuillez renseigner votre civilité.'}, widget=forms.Select(attrs={'class': 'form-control; col-md-6'}))

    first_name = forms.CharField(max_length=100, label="Prénom", error_messages={'required': 'Veuillez renseigner votre prénom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", error_messages={'required': 'Veuillez renseigner votre Nom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(format="%Y-%m-%d",attrs={'type': 'date', 'class': 'form-control'}), label="Date de naissance", error_messages={'required': 'Veuillez renseigner votre date de naissance.'})
    birth_city = forms.CharField(max_length=100, label="Ville de naissance", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #birth_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,label="Pays de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    nationality = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Nationalité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    #is_actual_country_as_birth_country = forms.BooleanField(label="Definir le pays actuel et la ville", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    actual_city = forms.CharField(max_length=100, label="Ville actuelle", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #actual_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,required=False, label="Pays actuel", widget=forms.Select(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, label="Code postal", widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=100, label="Adresse actuelle", error_messages={'required': 'Veuillez renseigner votre adresse.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, label="Téléphone", error_messages={'required': 'Veuillez renseigner votre téléphone.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession_situation = forms.ChoiceField(label="Situation professionnelle", error_messages={'required': 'Veuillez renseigner votre situation professionnelle.'}, widget=forms.Select(attrs={'class': 'form-control'}), choices=UserDetails.PROFESSION_SITUATION_CHOICES)
    activity_sector = forms.ChoiceField(choices=UserDetails.ACTIVITY_SECTOR_CHOICES, label="Secteur d'activité", error_messages={'required': 'Veuillez renseigner votre secteur d\'activité.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    profession = forms.ChoiceField(choices=UserDetails.PROFESSION_CHOICES, label="Profession", error_messages={'required': 'Veuillez renseigner votre profession.'}, widget=forms.Select(attrs={'class': 'form-control'}))

    # Champs de localisation (Région, Préfecture, Commune)
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label="Région",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )
    prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.none(),
        required=False,
        label="Préfecture",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_prefecture'})
    )
    commune = forms.ModelChoiceField(
        queryset=Commune.objects.none(),
        required=False,
        label="Commune",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_commune'})
    )
    quarter = forms.ModelChoiceField(
        queryset=Quarter.objects.none(),
        required=False,
        label="Quartier",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_quarter'})
    )

    class Meta:
            model = UserDetails
            fields = ['civility','first_name','last_name', 'birth_date','birth_city', 'nationality', 'actual_city', 'zip_code', 'address', 'phone', 'region', 'prefecture', 'commune', 'quarter']

    def __init__(self, *args, **kwargs):
        super(UserInfosForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_errors = True
        self.helper.error_text_inline = True  # Très important

        region_id = self.data.get(self.add_prefix('region'))
        prefecture_id = self.data.get(self.add_prefix('prefecture'))
        commune_id = self.data.get(self.add_prefix('commune'))

        if not region_id and self.initial.get('region'):
            val = self.initial.get('region')
            region_id = getattr(val, 'id', val)
        if not prefecture_id and self.initial.get('prefecture'):
            val = self.initial.get('prefecture')
            prefecture_id = getattr(val, 'id', val)
        if not commune_id and self.initial.get('commune'):
            val = self.initial.get('commune')
            commune_id = getattr(val, 'id', val)

        if not region_id and self.instance and self.instance.pk:
            region_id = self.instance.region_id
        if not prefecture_id and self.instance and self.instance.pk:
            prefecture_id = self.instance.prefecture_id
        if not commune_id and self.instance and self.instance.pk:
            commune_id = self.instance.commune_id

        try:
            if region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=int(region_id)).order_by('name')
            if prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=int(prefecture_id)).order_by('name')
            if commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune_id=int(commune_id)).order_by('name')
        except (ValueError, TypeError):
            pass


# Canonical profile forms used by the wizard.  Keep the model fields themselves
# for backwards-compatible data, but do not expose secondary profile metadata.
class UserInfosForm(forms.ModelForm):
    civility = forms.ChoiceField(
        choices=UserDetails.CIVILITY_CHOICES,
        required=False,
        label="Civilité",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(max_length=100, required=False, label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, label="Nom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, required=False, label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(
        required=False,
        label="Date de naissance",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    address = forms.CharField(max_length=100, required=False, label="Adresse", widget=forms.TextInput(attrs={'class': 'form-control'}))
    region = forms.ModelChoiceField(
        queryset=Region.objects.all().order_by('name'),
        required=False,
        label="Région",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )
    prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.none(),
        required=False,
        label="Préfecture",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_prefecture'})
    )
    commune = forms.ModelChoiceField(
        queryset=Commune.objects.none(),
        required=False,
        label="Commune",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_commune'})
    )
    quarter = forms.ModelChoiceField(
        queryset=Quarter.objects.none(),
        required=False,
        label="Quartier",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_quarter'})
    )

    class Meta:
        model = UserDetails
        fields = [
            'civility', 'first_name', 'last_name', 'phone', 'birth_date', 'address',
            'region', 'prefecture', 'commune', 'quarter',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        region_id = self.data.get(self.add_prefix('region'))
        prefecture_id = self.data.get(self.add_prefix('prefecture'))
        commune_id = self.data.get(self.add_prefix('commune'))

        if not region_id and self.instance and self.instance.pk:
            region_id = self.instance.region_id
        if not prefecture_id and self.instance and self.instance.pk:
            prefecture_id = self.instance.prefecture_id
        if not commune_id and self.instance and self.instance.pk:
            commune_id = self.instance.commune_id

        try:
            if region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=int(region_id)).order_by('name')
            if prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=int(prefecture_id)).order_by('name')
            if commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune_id=int(commune_id)).order_by('name')
        except (ValueError, TypeError):
            pass



class ProfileForm(PrivateDocumentValidationMixin, forms.ModelForm):
    class Meta:
        model = UserDetails
        fields = [
            'civility', 'first_name', 'last_name', 'phone', 'birth_date', 'address',
            'photo', 'id_card', 'id_card_country',
            'region', 'prefecture', 'commune', 'quarter',
        ]

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get('id_card') or getattr(self.instance, 'id_card', None)):
            cleaned['id_card_country'] = None
        return cleaned


class UserDocumentForm(PrivateDocumentValidationMixin, forms.ModelForm):
    photo = forms.ImageField(
        required=False,
        label="Photo de profil",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.webp'})
    )
    id_card = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png,.webp'}),
        label="Pièce d'identité (CNI ou Passeport)"
    )
    id_card_country = forms.ChoiceField(
        choices=UserDetails.COUNTRY_CHOICES,
        required=False,
        label="Pays d'émission de la pièce d'identité",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserDetails
        fields = ['photo', 'id_card', 'id_card_country']

    def clean(self):
        cleaned = super().clean()
        has_document = cleaned.get('id_card') or getattr(self.instance, 'id_card', None)
        if not has_document:
            cleaned['id_card_country'] = None
        return cleaned
    
class UserLinkForm(forms.ModelForm):
    facebook = forms.CharField(max_length=100, required=False, label="Facebook", widget=forms.TextInput(attrs={'class': 'form-control'}))
    twitter = forms.CharField(max_length=100, required=False, label="Twitter", widget=forms.TextInput(attrs={'class': 'form-control'}))
    linkedin = forms.CharField(max_length=100, required=False, label="Linkedin", widget=forms.TextInput(attrs={'class': 'form-control'}))
    instagram = forms.CharField(max_length=100, required=False, label="Instagram", widget=forms.TextInput(attrs={'class': 'form-control'}))
    website = forms.CharField(max_length=100, required=False, label="Site web", widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = UserDetails
        fields = ['facebook', 'twitter', 'linkedin', 'instagram', 'website']
   
class _LegacyProfileForm(PrivateDocumentValidationMixin, forms.ModelForm):
   
    #Model UserDetails fields
    user_category = forms.ChoiceField(choices=UserDetails.USER_CATEGORY_CHOICES, label="Catégorie d'utilisateur", widget=forms.Select(attrs={'class': 'form-control'}))
    civility = forms.ChoiceField(choices=UserDetails.CIVILITY_CHOICES, label="Civilité", error_messages={'required': 'Veuillez renseigner votre civilité.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, label="Prénom", error_messages={'required': 'Veuillez renseigner votre prénom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", error_messages={'required': 'Veuillez renseigner votre nom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Date de naissance", error_messages={'required': 'Veuillez renseigner votre date de naissance.'})
    birth_city = forms.CharField(max_length=100, label="Ville de naissance", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #birth_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,label="Pays de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    nationality = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Nationalité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    is_actual_country_as_birth_country = forms.BooleanField(label="Ville actuelle = Ville de naissance", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-control'}))
    actual_city = forms.CharField(max_length=100, label="Ville actuelle", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #actual_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays actuel", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, label="Code postal", error_messages={'required': 'Veuillez renseigner votre code postal.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=100, label="Adresse actuelle", error_messages={'required': 'Veuillez renseigner votre adresse.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, label="Téléphone", error_messages={'required': 'Veuillez renseigner votre téléphone.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession_situation = forms.ChoiceField(label="Situation professionnelle", widget=forms.Select(attrs={'class': 'form-control'}), choices=UserDetails.PROFESSION_SITUATION_CHOICES)
    activity_sector = forms.ChoiceField(choices=UserDetails.ACTIVITY_SECTOR_CHOICES, label="Secteur d'activité", error_messages={'required': 'Veuillez renseigner votre secteur d\'activité.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession = forms.ChoiceField(choices=UserDetails.PROFESSION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    high_education = forms.ChoiceField(choices=UserDetails.HIGH_EDUCATION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    person_contact  = forms.CharField(max_length=100, label="Personne à contacter", widget=forms.TextInput(attrs={'class': 'form-control'}))
   
    bio = forms.CharField(max_length=100, label="Biographie", widget=forms.TextInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    id_card = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Pièce d'identité")
    id_card_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, required=False, label="Pays", widget=forms.Select(attrs={'class': 'form-control'}))
    birth_piece = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Pièce de naissance")
    birth_piece_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, required=False, label="Pays", widget=forms.Select(attrs={'class': 'form-control'}))

    facebook = forms.CharField(max_length=100, label="Facebook", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    twitter = forms.CharField(max_length=100, label="Twitter", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    instagram = forms.CharField(max_length=100, label="Instagram", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    linkedin = forms.CharField(max_length=100, label="Linkedin", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label="Région",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )
    prefecture = forms.ModelChoiceField(
        queryset=Prefecture.objects.none(),
        required=False,
        label="Préfecture",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_prefecture'})
    )
    commune = forms.ModelChoiceField(
        queryset=Commune.objects.none(),
        required=False,
        label="Commune",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_commune'})
    )
    quarter = forms.ModelChoiceField(
        queryset=Quarter.objects.none(),
        required=False,
        label="Quartier",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_quarter'})
    )
    
    class Meta:
        model = UserDetails
        fields = ['civility', 'birth_date', 'birth_city','nationality', 'actual_city','zip_code', 'address', 'phone',
                  'photo', 'id_card', 'id_card_country', 'birth_piece', 'birth_piece_country',
                  'region', 'prefecture', 'commune', 'quarter'] 

    def clean(self):
        cleaned = super().clean()
        for document, country in (('id_card', 'id_card_country'), ('birth_piece', 'birth_piece_country')):
            has_document = cleaned.get(document) or getattr(self.instance, document, None)
            if not has_document:
                cleaned[country] = None
        return cleaned
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['birth_date'].required = True  # Rendre le champ obligatoire
        
        region_id = self.data.get(self.add_prefix('region'))
        prefecture_id = self.data.get(self.add_prefix('prefecture'))
        commune_id = self.data.get(self.add_prefix('commune'))

        if not region_id and self.initial.get('region'):
            val = self.initial.get('region')
            region_id = getattr(val, 'id', val)
        if not prefecture_id and self.initial.get('prefecture'):
            val = self.initial.get('prefecture')
            prefecture_id = getattr(val, 'id', val)
        if not commune_id and self.initial.get('commune'):
            val = self.initial.get('commune')
            commune_id = getattr(val, 'id', val)

        if not region_id and self.instance and self.instance.pk:
            region_id = self.instance.region_id
        if not prefecture_id and self.instance and self.instance.pk:
            prefecture_id = self.instance.prefecture_id
        if not commune_id and self.instance and self.instance.pk:
            commune_id = self.instance.commune_id

        try:
            if region_id:
                self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=int(region_id)).order_by('name')
            if prefecture_id:
                self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=int(prefecture_id)).order_by('name')
            if commune_id:
                self.fields['quarter'].queryset = Quarter.objects.filter(commune_id=int(commune_id)).order_by('name')
        except (ValueError, TypeError):
            pass
