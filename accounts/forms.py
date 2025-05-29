from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from page.models import  UserDetails
from django.utils.html import format_html
#from django.forms.widgets import RadioSelect
from django.forms.utils import flatatt
from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.html import strip_tags
from smtplib import SMTPException
from sosguinee import settings
import logging

from sosguinee.utils.utilities import Utilities
User = get_user_model()

logger = logging.getLogger(__name__)

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Identifiant (Email ou nom d'utilisateur)",
        widget=forms.TextInput(attrs={
            'class': 'validate',
            'placeholder': 'Entrez votre email ou nom d’utilisateur'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'validate',
            'placeholder': 'Entrez votre mot de passe',
            'id': 'password-field'      # ← on fixe un id simple
        })
    )

    def clean(self):
        cleaned = super().clean()
        ident = cleaned.get('username')
        pwd   = cleaned.get('password')

        if ident and pwd:
            # Backend personnalisé (voir plus haut) ou recherche manuelle
            user = authenticate(username=ident, password=pwd)
            if user is None:
                # on essaie de retrouver un user par email
                try:
                    user_obj = User.objects.get(Q(username__iexact=ident) | Q(email__iexact=ident))
                except User.DoesNotExist:
                    raise forms.ValidationError("Identifiant ou Mot de passe incorrect.")
                else:
                    if not user_obj.check_password(pwd):
                        raise forms.ValidationError("Identifiant ou Mot de passe incorrect.")
                    if not user_obj.is_active:
                        raise forms.ValidationError("Compte inactif.")
                    # si tout est ok on ré-authentifie
                    user = authenticate(username=user_obj.username, password=pwd)
            if user is None:
                # en dernier recours
                raise forms.ValidationError("Impossible de vous authentifier.")
            cleaned['user'] = user

        return cleaned


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'validate',
            'placeholder': 'Votre adresse email'
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
            'placeholder': 'Entrez votre mot de passe',
            'id': 'password-field'      # ← on fixe un id simple
        })
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'validate',
            'placeholder': 'Confirmez votre mot de passe',
            'id': 'password-field2'     # ← on fixe un id simple
        }),
        help_text="Entrez le même mot de passe que précédemment, pour vérification."
    )
    class Meta:
        model = User
        fields = ["civility", "first_name", "last_name", "username", "email", "password1", "password2"]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'validate', 'placeholder': 'Prénom'}),
            'last_name':  forms.TextInput(attrs={
                'class': 'validate', 'placeholder': 'Nom'}),
            'username':   forms.TextInput(attrs={
                'class': 'validate', 'placeholder': 'Nom d’utilisateur'}),
        }
        error_messages = {
            'username': {
                'required': "Veuillez renseigner un nom d’utilisateur.",
                'min_length': "Au moins 3 caractères.",
                'unique': "Ce nom d’utilisateur existe déjà."
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
        # crée User inactif + profil
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
                email=user.email
            )
        self._send_activation_email(user)
        
        return user

    def _send_activation_email(self, user):
        current_site = get_current_site(self.request)
        token = default_token_generator.make_token(user)
        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': user.pk,
            'token': token,
        }
        subject = "Activation de votre compte SOS Guinée"
        try:
            print("sending email")
            Utilities.sending_email("accounts/account_activation_email.html", [user.email], context, subject)
            print("email sent")
        except SMTPException as e:
            print("Erreur lors de l'envoi de l'email d'activation :", e)
            # loggez l’erreur, affichez un message utilisateur, etc.
            logger.error(f"Erreur SMTP : {e}")
            # # Optionnel : lever une ValidationError pour revenir au formulaire
            # raise forms.ValidationError(
            #     "Le service d’envoi d’email est temporairement indisponible, réessayez plus tard."
            # )


class UserInfosForm(forms.ModelForm):
    user_category = forms.ChoiceField(choices=UserDetails.USER_CATEGORY_CHOICES, required=True, label="Categorie d'utilisateur", error_messages={'required': 'Veuillez renseigner votre categorie d\'utilisateur.'}) 
    civility = forms.ChoiceField(choices=UserDetails.CIVILITY_CHOICES, label="Civilité", error_messages={'required': 'Veuillez renseigner votre civilité.'}, widget=forms.Select(attrs={'class': 'form-control; col-md-6'}))
    
    first_name = forms.CharField(max_length=100, label="Prénom", error_messages={'required': 'Veuillez renseigner votre prénom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", error_messages={'required': 'Veuillez renseigner votre Nom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(format="%Y-%m-%d",attrs={'type': 'date', 'class': 'form-control'}), label="Date de naissance", error_messages={'required': 'Veuillez renseigner votre date de naissance.'})
    birth_city = forms.CharField(max_length=100, label="Ville de naissance", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,label="Pays de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    nationality = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Nationalité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    is_actual_country_as_birth_country = forms.BooleanField(label="Definir le pays actuel et la ville", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    actual_city = forms.CharField(max_length=100, label="Ville actuelle", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    actual_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,required=False, label="Pays actuel", widget=forms.Select(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, label="Code postal", widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=100, label="Adresse actuelle", error_messages={'required': 'Veuillez renseigner votre adresse.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, label="Telephone", error_messages={'required': 'Veuillez renseigner votre telephone.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession_situation = forms.ChoiceField(label="Situation professionnelle", error_messages={'required': 'Veuillez renseigner votre situation professionnelle.'}, widget=forms.Select(attrs={'class': 'form-control'}), choices=UserDetails.PROFESSION_SITUATION_CHOICES)
    activity_sector = forms.ChoiceField(choices=UserDetails.ACTIVITY_SECTOR_CHOICES, label="Secteur d'activité", error_messages={'required': 'Veuillez renseigner votre secteur d\'activité.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    profession = forms.ChoiceField(choices=UserDetails.PROFESSION_CHOICES, label="Profession", error_messages={'required': 'Veuillez renseigner votre profession.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    high_education = forms.ChoiceField(choices=UserDetails.HIGH_EDUCATION_CHOICES, label="Niveau d'etudes", error_messages={'required': 'Veuillez renseigner votre niveau d\'etudes.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    person_contact  = forms.CharField(max_length=100, label="Personne à contacter", error_messages={'required': 'Veuillez renseigner votre personne à contacter.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
   
    class Meta:
        model = UserDetails
        fields = ['user_category', 'civility','first_name','last_name', 'birth_date','birth_city','birth_country',  'nationality', 'is_actual_country_as_birth_country', 'actual_city', 'actual_country', 'zip_code', 'address', 'phone', 'profession_situation', 'activity_sector', 'profession', 'high_education', 'person_contact']

    def clean(self):
        cleaned_data = super().clean()
        is_actual_country_as_birth_country = cleaned_data.get('is_actual_country_as_birth_country')
        actual_city = cleaned_data.get('actual_city')
        actual_country = cleaned_data.get('actual_country')

        if not is_actual_country_as_birth_country:
            if not actual_city:
                self.add_error('actual_city', 'Veuillez renseigner votre ville.')
            if not actual_country:
                self.add_error('actual_country', 'Veuillez renseigner votre pays.')

class UserDocumentForm(forms.ModelForm):
    bio = forms.CharField(max_length=100, required=False, label="Biographie", widget=forms.TextInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    id_card = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Pièce d'identité")
    id_card_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays d'acquisition de la pièce d'Identité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    birth_piece = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Carte de naissance")
    birth_piece_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays d'acquisition de la pièce de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
  
    class Meta:
        model = UserDetails
        fields = ['photo', 'id_card', 'id_card_country', 'birth_piece', 'birth_piece_country','bio'] 
    
class UserLinkForm(forms.ModelForm):
    facebook = forms.CharField(max_length=100, required=False, label="Facebook", widget=forms.TextInput(attrs={'class': 'form-control'}))
    twitter = forms.CharField(max_length=100, required=False, label="Twitter", widget=forms.TextInput(attrs={'class': 'form-control'}))
    linkedin = forms.CharField(max_length=100, required=False, label="Linkedin", widget=forms.TextInput(attrs={'class': 'form-control'}))
    instagram = forms.CharField(max_length=100, required=False, label="Instagram", widget=forms.TextInput(attrs={'class': 'form-control'}))
    website = forms.CharField(max_length=100, required=False, label="Site web", widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = UserDetails
        fields = ['facebook', 'twitter', 'linkedin', 'instagram', 'website']
   
class ProfileForm(forms.ModelForm):
   
    #Model UserDetails fields
    user_category = forms.ChoiceField(choices=UserDetails.USER_CATEGORY_CHOICES, label="Catégorie d'utilisateur", widget=forms.Select(attrs={'class': 'form-control'}))
    civility = forms.ChoiceField(choices=UserDetails.CIVILITY_CHOICES, label="Civilité", error_messages={'required': 'Veuillez renseigner votre civilité.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, label="Prénom", error_messages={'required': 'Veuillez renseigner votre prénom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", error_messages={'required': 'Veuillez renseigner votre nom.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Date de naissance", error_messages={'required': 'Veuillez renseigner votre date de naissance.'})
    birth_city = forms.CharField(max_length=100, label="Ville de naissance", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES,label="Pays de naissance", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    nationality = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Nationalité", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    is_actual_country_as_birth_country = forms.BooleanField(label="Ville actuelle = Ville de naissance", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-control'}))
    actual_city = forms.CharField(max_length=100, label="Ville actuelle", error_messages={'required': 'Veuillez renseigner votre ville.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    actual_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays actuel", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    zip_code = forms.CharField(max_length=10, label="Code postal", error_messages={'required': 'Veuillez renseigner votre code postal.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(max_length=100, label="Adresse actuelle", error_messages={'required': 'Veuillez renseigner votre adresse.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, label="Telephone", error_messages={'required': 'Veuillez renseigner votre telephone.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession_situation = forms.ChoiceField(label="Situation professionnelle", widget=forms.Select(attrs={'class': 'form-control'}), choices=UserDetails.PROFESSION_SITUATION_CHOICES)
    activity_sector = forms.ChoiceField(choices=UserDetails.ACTIVITY_SECTOR_CHOICES, label="Secteur d'activité", error_messages={'required': 'Veuillez renseigner votre secteur d\'activité.'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
    profession = forms.Select(choices=UserDetails.PROFESSION_CHOICES, attrs={'class': 'form-control'})
    high_education = forms.Select(choices=UserDetails.HIGH_EDUCATION_CHOICES, attrs={'class': 'form-control', 'placeholder': 'Ecole', } )
    person_contact  = forms.CharField(max_length=100, label="Personne à contacter", widget=forms.TextInput(attrs={'class': 'form-control'}))
   
    bio = forms.CharField(max_length=100, label="Biographie", widget=forms.TextInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    id_card = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Pièce d'identité")
    id_card_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))
    birth_piece = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}), label="Pièce de naissance")
    birth_piece_country = forms.ChoiceField(choices=UserDetails.COUNTRY_CHOICES, label="Pays", error_messages={'required': 'Veuillez renseigner votre pays.'}, widget=forms.Select(attrs={'class': 'form-control'}))

    facebook = forms.CharField(max_length=100, label="Facebook", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    twitter = forms.CharField(max_length=100, label="Twitter", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    instagram = forms.CharField(max_length=100, label="Instagram", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    linkedin = forms.CharField(max_length=100, label="Linkedin", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = UserDetails
        fields = ['user_category', 'civility', 'birth_date', 'birth_city','birth_country', 'nationality', 'actual_city', 'actual_country', 'zip_code', 'address', 'phone',
                  'profession_situation', 'activity_sector', 'profession', 'high_education', 'person_contact', 'bio', 'photo', 'id_card', 'id_card_country', 'birth_piece', 'birth_piece_country',
                  'facebook', 'twitter', 'instagram', 'linkedin'] 
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['birth_date'].required = True  # Rendre le champ obligatoire