from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormView
from formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from page.models import UserDetails, LossAlert, FundingRequest, Donation, FundPayment, MessageContact, Comment
from ..forms import ProfileForm, UserInfosForm, UserDocumentForm, UserLinkForm

@login_required
def user_profile(request):
    if request.user.is_authenticated:
        try:
            # Sécurise le fetch même s'il y a des doublons inattendus
            profile = (
                UserDetails.objects.filter(user=request.user)
                .order_by('-created_at')
                .first()
            )
            if profile is None:
                profile = UserDetails.objects.create(user=request.user)
            user_details = ProfileForm(instance=profile)

            # Récupérer les éléments créés par l'utilisateur
            alerts = LossAlert.objects.filter(created_by=request.user).order_by('-created_at')
            funding_requests = FundingRequest.objects.filter(created_by=request.user).order_by('-created_at')
            donations = Donation.objects.filter(donor_email=request.user.email).order_by('-created_at')
            # Paiements (financements effectués)
            fundings = FundPayment.objects.filter(donor_email=request.user.email).order_by('-created_at')
            # Messages de contact envoyés
            messages_sent = MessageContact.objects.filter(email=request.user.email).order_by('-created_at')
            # Commentaires postés
            comments = Comment.objects.filter(user=request.user).order_by('-created_at')

            countries = dict(UserDetails.COUNTRY_CHOICES)
            country = countries.get(profile.birth_country, 'Non renseigne')

            nationality = countries.get(profile.nationality, 'Non renseigne')

            civilities = dict(UserDetails.CIVILITY_CHOICES)
            civility = civilities.get(profile.civility, 'Non renseigne')

            professions = dict(UserDetails.PROFESSION_CHOICES)
            profession = professions.get(profile.profession, 'Non renseigne')

            categories = dict(UserDetails.USER_CATEGORY_CHOICES)
            category = categories.get(profile.user_category, 'Non renseigne')
            account_status = profile.user_status or 'Inactive'

            context = {
                'profile': profile,
                'country': country,
                'civility': civility,
                'profession': profession,
                'nationality': nationality,
                'category': category,
                'account_status': account_status,
                'alerts': alerts,
                'funding_requests': funding_requests,
                'donations': donations,
                'fundings': fundings,
                'messages_sent': messages_sent,
                'comments': comments,
            }

            return render(request, 'accounts/profil.html', context)
        except UserDetails.DoesNotExist:
            return redirect('login')
    else:
        return redirect('home')

class UserInfosView(FormView):
    template_name = 'accounts/user_infos.html'
    form_class = UserInfosForm
    success_url = 'user-document'

    def form_valid(self, form):
        return super().form_valid(form)

class UserDocumentView(FormView):
    template_name = 'accounts/user_document.html'
    form_class = UserDocumentForm
    success_url = 'user-link'

    def form_valid(self, form):
        return super().form_valid(form)

class UserLinkView(FormView):
    template_name = 'accounts/user_link.html'
    form_class = UserLinkForm
    success_url = 'update_profile'

    def form_valid(self, form):
        return super().form_valid(form)

FORMS = [
    ("user_infos", UserInfosForm),
    ("user_document", UserDocumentForm),
    ("user_link", UserLinkForm),
]

TEMPLATES = {
    "user_infos": "accounts/user_infos.html",
    "user_document": "accounts/user_document.html",
    "user_link": "accounts/user_link.html",
}

class UpdateUserProfileWizard(SessionWizardView):
    form_list = FORMS
    file_storage = FileSystemStorage(location='/tmp')
    
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    def get_template_names(self):
        step = self.steps.current
        if step in TEMPLATES:
            return [TEMPLATES[step]]
        raise Exception(f"Template non défini pour l'étape {step}")

    def get_form_instance(self, step):
        """Pré-remplir avec les données existantes de l'utilisateur."""
        if not hasattr(self, 'user_details'):
            try:
                self.user_details = UserDetails.objects.get(user=self.request.user)
            except UserDetails.DoesNotExist:
                self.user_details = UserDetails(user=self.request.user)
        return self.user_details

    def done(self, form_list, **kwargs):
        user_details, _ = UserDetails.objects.get_or_create(user=self.request.user)

        for form in form_list:
            for key, value in form.cleaned_data.items():
                # Handle location fields specially (they are model FKs)
                if key in ('region', 'prefecture', 'commune'):
                    setattr(user_details, f'{key}_id', value.id if value else None)
                else:
                    setattr(user_details, key, value)

        user_details.save()
        return redirect('/profile')
