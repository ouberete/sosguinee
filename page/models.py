from datetime import datetime
from email.policy import default
from random import choices
import uuid
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey

from page.middleware import get_current_user


class BaseEntity(models.Model):
    # Final: enforce uniqueness and non-null after backfill
    public_id = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #id = models.UUIDField(primary_key=True, )
    isDeleted = models.BooleanField(blank=True, null=True, default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_%(class)s_set'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_%(class)s_set'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_%(class)s_set'
    )
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if not getattr(current_user, "is_authenticated", False):
            current_user = None
        if not self.pk:  # Si c'est une création
            self.created_by = current_user
        else:  # Sinon, c'est une mise à jour
            self.updated_by = current_user
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        current_user = get_current_user()
        if not getattr(current_user, "is_authenticated", False):
            current_user = None
        self.isDeleted = True
        self.deleted_by = current_user
        self.save()

class BaseManager(models.Manager):
    """
    Manager de base qui exclut les objets marqués comme supprimés.
    """

    def get_queryset(self):
        return super().get_queryset().filter(isDeleted=False)


class AllObjectsManager(models.Manager):
    """
    Manager alternatif pour inclure les objets supprimés.
    """

    def get_queryset(self):
        return super().get_queryset()

Gender = (
    ('Male', 'Masculin'),
    ('Female', 'Feminin'),
)

# --- Location hierarchy: Region > Prefecture > Commune > Quarter ---
class Region(BaseEntity):
    name = models.CharField(max_length=255, unique=True, verbose_name='Région')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Région'
        verbose_name_plural = 'Régions'
        db_table = 'region'

    def __str__(self):
        return self.name


class Prefecture(BaseEntity):
    region = models.ForeignKey('Region', on_delete=models.PROTECT, related_name='prefectures', verbose_name='Région')
    name = models.CharField(max_length=255, verbose_name='Préfecture')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        unique_together = ('region', 'name')
        verbose_name = 'Préfecture'
        verbose_name_plural = 'Préfectures'
        db_table = 'prefecture'

    def __str__(self):
        return f"{self.name}"


class Commune(BaseEntity):
    prefecture = models.ForeignKey('Prefecture', on_delete=models.PROTECT, related_name='communes', verbose_name='Préfecture')
    name = models.CharField(max_length=255, verbose_name='Commune')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        unique_together = ('prefecture', 'name')
        verbose_name = 'Commune'
        verbose_name_plural = 'Communes'
        db_table = 'commune'

    def __str__(self):
        return f"{self.name}"


class Quarter(BaseEntity):
    commune = models.ForeignKey('Commune', on_delete=models.PROTECT, related_name='quarters', verbose_name='Commune')
    name = models.CharField(max_length=255, verbose_name='Quartier')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        unique_together = ('commune', 'name')
        verbose_name = 'Quartier'
        verbose_name_plural = 'Quartiers'
        db_table = 'quarter'

    def __str__(self):
        return f"{self.name}"

class FundingType(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Type Financement', unique=True)
    description = models.TextField(verbose_name='Description Type Financement')
    objects = BaseManager()
    all_objects = AllObjectsManager()
    class Meta:
        verbose_name = 'Type Financement'
        verbose_name_plural = 'Types Financements'
        db_table = 'funding_type'
        
    def __str__(self):
        return self.name

class LossAlertType(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Type alerte perte', unique=True)
    description = models.TextField(verbose_name='Description Type alerte perte')
    objects = BaseManager()
    all_objects = AllObjectsManager()
    class Meta:
        verbose_name = 'Type alerte perte'
        verbose_name_plural = 'Types alerte perte'
        db_table = 'loss_alert_type'
        
        
    def __str__(self):
        return self.name

class LossAlertStatus(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Statut alerte perte', unique=True)
    description = models.TextField(verbose_name='Description Statut alerte perte')
    objects = BaseManager()
    all_objects = AllObjectsManager()
    class Meta:
        verbose_name = 'Statut alerte perte'
        verbose_name_plural = 'Statuts alerte perte'
        db_table = 'loss_alert_status'
        
    def __str__(self):
        return self.name

class FundingRequestStatus(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Statut Financement', unique=True)
    description = models.TextField(verbose_name='Description Statut Financement')
    objects = BaseManager()
    all_objects = AllObjectsManager()
        
    class Meta:
        verbose_name = 'Statut Financement'
        verbose_name_plural = 'Statuts Financements'
        db_table = 'funding_request_status'

    def __str__(self):
        return self.name

UserStatus = (
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Blocked', 'Blocked'),
)

""" 
class UserDetails(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=255, null=True, blank=True)
    telephone = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=Gender)
    user_status = models.CharField(max_length=255, choices=UserStatus, default='Inactive') 
    
"""

class OptionalAlertDoc(BaseEntity):
    document = models.FileField(upload_to='img/alerts/', verbose_name='Autres documents', blank=True, null=True)
    document_name = models.CharField(max_length=255, verbose_name='Nom document', blank=True, null=True)
    document_type = models.CharField(max_length=255, verbose_name='Type document', blank=True, null=True)
    document_size = models.CharField(max_length=255, verbose_name='Taille document', blank=True, null=True)
  
    class Meta:
        verbose_name = "Autre documents d'alerte perte"
        verbose_name_plural = "Autres documents d' alerte perte"
        db_table = 'optional_alert_doc'

class LossAlert(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Nom du sujet concerné')
    loss_alert_type = models.ForeignKey(LossAlertType, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Type alerte perte')
    loss_alert_status = models.ForeignKey(LossAlertStatus, on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField(verbose_name='Description')
    principal_image = models.ImageField(upload_to='img/alerts/', blank=True, null=True, verbose_name='Image Principale')
    email = models.CharField(max_length=255, null=True, blank=True, verbose_name='Email')
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Telephone')
    country = models.CharField(max_length=255, default="Guinée", blank=True, null=True, verbose_name='Pays')
    region = models.ForeignKey('Region', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Région')
    prefecture = models.ForeignKey('Prefecture', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Préfecture')
    commune = models.ForeignKey('Commune', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Commune')
    quarter = models.ForeignKey('Quarter', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Quartier')
    address = models.CharField(max_length=255, verbose_name='Adresse')
    date_alert = models.DateField(verbose_name='Date alerte perte')
    hour_alert = models.TimeField(blank=True, null=True, verbose_name='Heure alerte perte')
    optional_docs = models.ManyToManyField(OptionalAlertDoc, verbose_name='Autres documents', blank=True, related_name='loss_alert')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    @property
    def type_alert_name(self):
        if self.loss_alert_type:
            return self.loss_alert_type.name
        else:
            return "Alerte Perte"
    
    @property
    def status_alert_name(self):
        if self.loss_alert_status:
            return self.loss_alert_status.name 
        else :
            return "Statut non defini"
        
    class Meta:
        verbose_name = 'Alerte perte'
        verbose_name_plural = 'Alertes perte'
        db_table = 'loss_alert'
        
    def add_docs(self, docs):
        for doc in docs:
            # Create a new OptionalAlertDoc instance
            dc = OptionalAlertDoc()
            dc.document = doc  # Assign the file directly to the document field
            dc.document_name = doc.name
            dc.document_type = doc.content_type
            dc.document_size = doc.size
            dc.save()
            self.optional_docs.add(dc)

class OptionalFundingDoc(BaseEntity):
    document = models.FileField(upload_to='img/Fundings/', verbose_name='Autres documents', blank=True, null=True)
    document_name = models.CharField(max_length=255, verbose_name='Nom document', blank=True, null=True)
    document_type = models.CharField(max_length=255, verbose_name='Type document', blank=True, null=True)
    document_size = models.CharField(max_length=255, verbose_name='Taille document', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Autre document de Financement'
        verbose_name_plural = 'Autres documents de Financements'
        db_table = 'optional_funding_doc'

class FundingRequest(BaseEntity):
    beneficiary_name = models.CharField(max_length=255, verbose_name='Nom Beneficiaire')
    title = models.CharField(max_length=255, verbose_name='Intitulé Financement', blank=True, null=True)
    funding_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant Financement')
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant reçu", default=0)
    funding_request_status = models.ForeignKey(FundingRequestStatus, on_delete=models.PROTECT, blank=True, null=True)
    funding_request_type = models.ForeignKey(FundingType, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Type Financement')
    description_needs = models.TextField(verbose_name='Description besoins')
    principal_image = models.ImageField(upload_to='img/Fundings/', verbose_name='Image Principale')
    optional_docs = models.ManyToManyField(OptionalFundingDoc, blank=True, verbose_name='Autres documents', related_name='funding_request')
    email = models.CharField(max_length=255, null=True, blank=True, verbose_name='Email')
    phone = models.CharField(max_length=255, verbose_name='Telephone', blank=True, null=True)
    country = models.CharField(max_length=255, default="Guinée", blank=True, null=True)
    region = models.ForeignKey('Region', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Région')
    prefecture = models.ForeignKey('Prefecture', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Préfecture')
    commune = models.ForeignKey('Commune', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Commune')
    quarter = models.ForeignKey('Quarter', on_delete=models.PROTECT, blank=True, null=True, verbose_name='Quartier')
    address = models.CharField(max_length=255, verbose_name='Adresse', blank=True, null=True)
    end_date = models.DateField(verbose_name='Date Fin Financement', blank=True, null=True)
    start_date = models.DateField(verbose_name='Date Debut Demande', default=timezone.now, blank=True, null=True)
    objects = BaseManager()
    all_objects = AllObjectsManager()

    @property
    def progress(self):
        if self.funding_amount > 0:
            mr = self.amount_received if self.amount_received else 0
            return int((mr / self.funding_amount) * 100)
        return 0

    @property
    def days_remaining(self):
        today = datetime.today().date()
        print(self.end_date)
        if  self.end_date and self.end_date >= today:
            return (self.end_date - today).days
        
        return "N/A"
    
    @property
    def funding_request_type_name(self):
        if self.funding_request_type:
            return self.funding_request_type.name
        else :
            return "Demande de financement"
        
    @property 
    def funding_request_status_name(self):
        if self.funding_request_status:
            return self.funding_request_status.name
        else :
            return "Non defini"
    
    class Meta:
        verbose_name = 'Demande Financement'
        verbose_name_plural = 'Demandes Financements'
        db_table = 'funding_request'
        
    def add_funding_docs(self, docs):
        for doc in docs:
            # Create a new OptionalAlertDoc instance
            dc = OptionalFundingDoc()
            dc.document = doc  # Assign the file directly to the document field
            dc.document_name = doc.name
            dc.document_type = doc.content_type
            dc.document_size = doc.size
            dc.save()
            self.optional_docs.add(dc)

    @property
    def remaining_amount(self):
        return max(self.funding_amount - self.amount_received, 0)

#USer details
class UserDetails(BaseEntity):
    MADAME = 'Mme'
    MONSIEUR = 'Mr'
    USER_CATEGORY_CHOICES = [
        ('', 'Choisir catégorie'),
        ('PPHYSIQUE', 'Physique'),
        ('PMORALE', 'Morale'),
    ]
    COUNTRY_CHOICES = [
        ('GN', 'Guinée'),
        ('FR', 'France'),
        ('US', 'États-Unis d\'Amérique'),
        ('ES', 'Espagne'),
        ('GB', 'Royaume-Uni'),
        ('CA', 'Canada'),
        ('DE', 'Allemagne'),
        ('IT', 'Italie'),
        ('JP', 'Japon'),
        ('AU', 'Australie'),
        ('BR', 'Brésil'),
        ('IN', 'Inde'),
        ('CH', 'Chine'),
        ('NL', 'Pays-Bas'),
        ('MX', 'Mexique'),
        ('AR', 'Argentine'),
        ('IE', 'Irlande'),
        ('RU', 'Russie'),
        ('SN', 'Sénégal'),
        ('ML', 'Mali'),
        ('ZA', 'Afrique du Sud'),
        ('KE', 'Kenya'),
        ('NG', 'Nigéria'),
        ('GH', 'Ghana'),
        ('LR', 'Libéria'),
        ('CM', 'Cameroun'),
        ('TN', 'Tunisie'),
        ('DZ', 'Algérie'),
        ('EG', 'Égypte'),
        ('SL', 'Sierra-Leone'),
        ('GM', 'Gambie')
    ]
    CIVILITY_CHOICES = [
        ('', 'Choisir civilité'),
        (MADAME, 'Madame'),
        (MONSIEUR, 'Monsieur'),
    ]

    ACTIVITY_SECTOR_CHOICES = [
        ('', 'Choisir secteur d\'activité'),
        ('AGRICULTURE', 'Agriculture'),
        ('CONSTRUCTION', 'Construction'),
        ('INDUSTRIAL', 'Industrielle'),
        ('COMMERCE', 'Commerce'),
        ('TECHNOLOGY', 'Technologie'),
        ('OTHER', 'Autre'),
    ]

    HIGH_EDUCATION_CHOICES = [
        ('', 'Choisir dernier diplôme'),
        ('BACCALAUREAT', 'Baccalauréat'),
        ('BTS', 'BTS'),
        ('LICENCE', 'Licence'),
        ('MASTER', 'Master'),
        ('DOCTORAT', 'Doctorat'),
        ('OTHER', 'Autre'),
    ]

    PROFESSION_SITUATION_CHOICES = [
        ('', 'Choisir situation professionnelle'),
        ('EMPLOYED', 'Employé'),
        ('UNEMPLOYED', 'Sans emploi'),
        ('OTHER', 'Autre'),
    ]

    PROFESSION_CHOICES = [
        ('', 'Choisir profession'),
        ('TECHNICIAN', 'Technicien'),
        ('PROFESSIONAL', 'Professionnel'),
        ('OTHER', 'Autre'),
    ]

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='details')
    civility = models.CharField(max_length=5, choices=CIVILITY_CHOICES, blank=True, null=True, verbose_name='Civilité')
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    id_card = models.FileField(upload_to='user_images/id_cards', blank=True, null=True)
    id_card_type = models.CharField(max_length=100, blank=True, null=True)
    id_card_country = models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_CHOICES)
    birth_piece = models.FileField(upload_to='user_images/birth_piece', blank=True, null=True)
    birth_piece_country = models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_CHOICES)
    person_contact = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to='user_images/photos', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    birth_place = models.CharField(max_length=100, blank=True, null=True)
    profession = models.CharField(max_length=100, choices=PROFESSION_CHOICES, blank=True, null=True, verbose_name='Profession', editable=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    actual_country = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    birth_country = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    is_actual_country_as_birth_country = models.BooleanField(default=True)
    phone_code = models.CharField(max_length=5, blank=True, null=True)
    profession_situation = models.CharField(max_length=100, blank=True, null=True, choices=PROFESSION_SITUATION_CHOICES)
    activity_sector = models.CharField(max_length=100, blank=True, null=True, choices=ACTIVITY_SECTOR_CHOICES)
    high_education = models.CharField(max_length=100, blank=True, null=True, choices=HIGH_EDUCATION_CHOICES)
    nationality = models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_CHOICES)
    birth_city = models.CharField(max_length=100, blank=True, null=True)
    actual_city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    linkedin = models.CharField(max_length=100, blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=[('Creator', 'Creator'), ('Backer', 'Backer')], default='Creator')
    user_category = models.CharField(max_length=20, choices=USER_CATEGORY_CHOICES, blank=True, null=True)
    user_status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Detail Utilisateur'
        verbose_name_plural = 'Details Utilisateurs'
        db_table = 'user_details'
    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return f'/users/{self.user.id}'
  
  
class MessageContact(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Nom')
    email = models.CharField(max_length=255, verbose_name='Email')
    subject = models.CharField(max_length=255, verbose_name='Sujet', blank=True, null=True)
    message = models.TextField(verbose_name='Message')
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Telephone')
    date_contact = models.DateTimeField(default=timezone.now, verbose_name='Date de contact', blank=True, null=True)
    is_read = models.BooleanField(default=False, verbose_name='Lu')

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        db_table = 'contact_message'
        
class Donation(BaseEntity):
    PAYMENT_METHODS = (
        ('paycard', 'PayCard'),
        ('stripe', 'Stripe'),
        ('orange_money', 'Orange Money'),
        ('paypal', 'PayPal'),
        ('autre', 'Autre'),
    )

    STATUS_CHOICES = (
        ('en_attente', 'En attente'),
        ('réussi', 'Réussi'),
        ('échoué', 'Échoué'),
    )
    donor_first_name = models.CharField(max_length=255, verbose_name='Nom Donateur', blank=True, null=True)
    donor_last_name = models.CharField(max_length=255, verbose_name='Nom Donateur', blank=True, null=True)
    donor_phone = models.CharField(max_length=20, verbose_name='Téléphone Donateur', blank=True, null=True)
    donor_country = models.CharField(choices=UserDetails.COUNTRY_CHOICES,max_length=255, verbose_name='Pays Donateur', blank=True, null=True)
    donor_city = models.CharField(max_length=255, verbose_name='Ville Donateur', blank=True, null=True)
    donor_quarter = models.CharField(max_length=255, verbose_name='Quartier Donateur', blank=True, null=True)
    donor_email = models.EmailField(verbose_name='Email Donateur', blank=True, null=True)
    donor_address = models.CharField(max_length=255, verbose_name='Adresse Donateur', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations', blank=True, null=True, verbose_name='Donateur')
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Montant')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal', verbose_name='Méthode de paiement')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    transaction_id = models.CharField(max_length=255, verbose_name='ID Transaction', blank=True, null=True)
    reference = models.CharField(max_length=100, unique=True, verbose_name='Référence de don', help_text='Référence unique pour le don', blank=True, null=True)
    donation_date = models.DateTimeField(default=timezone.now, verbose_name='Date Don', blank=True, null=True)
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Don'
        verbose_name_plural = 'Dons'
        db_table = 'donation'

    def __str__(self):
        return f"{self.amount} GNF via {self.method} - {self.status}"
        
class EmailContent(BaseEntity):
    subjet = models.TextField(blank=True, null=True, verbose_name="Object du message")
    plain_message = models.TextField(blank=True, null=True, verbose_name='Message Texte')
    sender_email = models.TextField(blank=True, null=True, verbose_name='Envoyeur')
    receiver_email =  models.TextField(blank=True, null=True, verbose_name='Beneficiaire'), 
    html_message = models.TextField(blank=True, null=True, verbose_name='Message Html')
    is_sent = models.BooleanField(default=False)
    date_sent = models.DateTimeField(blank=True, null=True)
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'
        db_table = 'email_content'


class FundingRequestNotification(BaseEntity):
    funding_request = models.ForeignKey(FundingRequest, on_delete=models.CASCADE, related_name='notifications', verbose_name='Demande de financement')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='funding_notifications', verbose_name='Utilisateur')
    message = models.TextField(verbose_name='Message de notification')
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    date_notification = models.DateTimeField(default=timezone.now, verbose_name='Date de notification')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Notification de demande de financement'
        verbose_name_plural = 'Notifications de demandes de financement'
        db_table = 'funding_request_notification'

    def __str__(self):
        return f"Notification for {self.user.username} - {self.funding_request.title} - {self.date_notification.strftime('%Y-%m-%d %H:%M:%S')}"
    def mark_as_read(self):
        self.is_read = True
        self.save()
    def mark_as_unread(self):
        self.is_read = False
        self.save()

class LossAlertNotification(BaseEntity):
    loss_alert = models.ForeignKey(LossAlert, on_delete=models.CASCADE, related_name='notifications', verbose_name='Alerte de perte')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loss_notifications', verbose_name='Utilisateur')
    message = models.TextField(verbose_name='Message de notification')
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    date_notification = models.DateTimeField(default=timezone.now, verbose_name='Date de notification')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Notification d\'alerte de perte'
        verbose_name_plural = 'Notifications d\'alertes de perte'
        db_table = 'loss_alert_notification'

    def __str__(self):
        return f"Notification for {self.user.username} - {self.loss_alert.title} - {self.date_notification.strftime('%Y-%m-%d %H:%M:%S')}"
    def mark_as_read(self):
        self.is_read = True
        self.save()
    def mark_as_unread(self):
        self.is_read = False
        self.save()
class FundPayment(BaseEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='fund_payments', verbose_name='Utilisateur')
    donor_first_name = models.CharField(max_length=255, verbose_name='Prenom Donateur', blank=True, null=True)
    donor_last_name = models.CharField(max_length=255, verbose_name='Nom Donateur', blank=True, null=True)
    donor_phone = models.CharField(max_length=20, verbose_name='Téléphone Donateur', blank=True, null=True)
    donor_country = models.CharField(choices=UserDetails.COUNTRY_CHOICES,max_length=255, verbose_name='Pays Donateur', blank=True, null=True)
    donor_city = models.CharField(max_length=255, verbose_name='Ville Donateur', blank=True, null=True)
    donor_quarter = models.CharField(max_length=255, verbose_name='Quartier Donateur', blank=True, null=True)
    donor_email = models.EmailField(verbose_name='Email Donateur', blank=True, null=True)
    donor_address = models.CharField(max_length=255, verbose_name='Adresse Donateur', blank=True, null=True)
    transaction_id = models.CharField(max_length=255, verbose_name='ID Transaction', blank=True, null=True)
    funding_request = models.ForeignKey(FundingRequest, on_delete=models.CASCADE, related_name='payments', verbose_name='Demande de financement')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant')
    payment_method = models.CharField(max_length=20, choices=Donation.PAYMENT_METHODS, default='PayCard', verbose_name='Méthode de paiement')
    status = models.CharField(max_length=20, choices=Donation.STATUS_CHOICES, default='en_attente', verbose_name='Statut')
    reference = models.CharField(max_length=100, unique=True, verbose_name='Référence de paiement', help_text='Référence unique pour le paiement', blank=True, null=True)
    payment_date = models.DateTimeField(default=timezone.now, verbose_name='Date de paiement')
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Paiement de financement'
        verbose_name_plural = 'Paiements de financements'
        db_table = 'fund_payment'

    def __str__(self):
        return f"{self.amount} GNF via {self.payment_method} - {self.status} - {self.funding_request.title}"


class Comment(BaseEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    rating = models.DecimalField(null=True, blank=True, default=0.0, decimal_places=0, max_digits=5)
    text = models.TextField("Commentaire", max_length=1000)
    objects = BaseManager()
    all_objects = AllObjectsManager()

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['-created_at']
        db_table = 'Commentaire'


class Report(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.TextField(verbose_name="Raison du signalement", max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'signalement'
        unique_together = ('comment', 'reporter')  # Pour éviter plusieurs signalements par le même utilisateur
        verbose_name = "Signalement"
        verbose_name_plural = "Signalements"

    def __str__(self):
        return f"Signalement par {self.reporter.username} sur {self.comment.id}"

