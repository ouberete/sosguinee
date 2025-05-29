from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BaseEntity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #id = models.UUIDField(primary_key=True, )
    class Meta:
        abstract = True

Gender = (
    ('Male', 'Masculin'),
    ('Female', 'Feminin'),
)

class FundingType(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Type Financement', unique=True)
    description = models.TextField(verbose_name='Description Type Financement')
    class Meta:
        verbose_name = 'Type Financement'
        verbose_name_plural = 'Types Financements'
        db_table = 'funding_type'
        
    def __str__(self):
        return self.name

class LossAlertType(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Type alerte perte', unique=True)
    description = models.TextField(verbose_name='Description Type alerte perte')
            
    class Meta:
        verbose_name = 'Type alerte perte'
        verbose_name_plural = 'Types alerte perte'
        db_table = 'loss_alert_type'
        
        
    def __str__(self):
        return self.name

class LossAlertStatus(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Statut alerte perte', unique=True)
    description = models.TextField(verbose_name='Description Statut alerte perte')
       
    class Meta:
        verbose_name = 'Statut alerte perte'
        verbose_name_plural = 'Statuts alerte perte'
        db_table = 'loss_alert_status'
        
    def __str__(self):
        return self.name

class FundingRequestStatus(BaseEntity):
    name = models.CharField(max_length=255, verbose_name='Statut Financement', unique=True)
    description = models.TextField(verbose_name='Description Statut Financement')
    
        
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
    name = models.CharField(max_length=255, verbose_name='Nom')
    loss_alert_type = models.ForeignKey(LossAlertType, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Type alerte perte')
    loss_alert_status = models.ForeignKey(LossAlertStatus, on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField(verbose_name='Description')
    principal_image = models.ImageField(upload_to='img/alerts/', blank=True, null=True, verbose_name='Image Principale')
    email = models.CharField(max_length=255, null=True, blank=True, verbose_name='Email')
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Telephone')
    country = models.CharField(max_length=255, default="Guinée", blank=True, null=True, verbose_name='Pays')
    city = models.CharField(max_length=255, verbose_name='Ville')
    quarter = models.CharField(max_length=255, verbose_name='Quartier')
    address = models.CharField(max_length=255, verbose_name='Adresse')
    date_alert = models.DateField(verbose_name='Date alerte perte')
    hour_alert = models.TimeField(blank=True, null=True, verbose_name='Heure alerte perte')
    optional_docs = models.ManyToManyField(OptionalAlertDoc, blank=True, related_name='loss_alert')

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
    city = models.CharField(max_length=255, verbose_name='Ville')
    quarter = models.CharField(max_length=255, verbose_name='Quartier', blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name='Adresse', blank=True, null=True)
    end_date = models.DateField(verbose_name='Date Fin Financement', blank=True, null=True)
    start_date = models.DateField(verbose_name='Date Debut Demande', default=timezone.now, blank=True, null=True)
    
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
        
    def add_docs(self, docs):
        for doc in docs:
            # Create a new OptionalAlertDoc instance
            dc = OptionalFundingDoc()
            dc.document = doc  # Assign the file directly to the document field
            dc.document_name = doc.name
            dc.document_type = doc.content_type
            dc.document_size = doc.size
            dc.save()
            self.optional_docs.add(dc)


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
        ('', 'Choisir Pays'),
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
        ('GN', 'Guinée'),
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
    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        db_table = 'contact_message'
        
class Donation(BaseEntity):
    PAYMENT_METHODS = (
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations', blank=True, null=True, verbose_name='Donateur')
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Montant')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal', verbose_name='Méthode de paiement')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    reference = models.CharField(max_length=100, unique=True)
    date_donation = models.DateTimeField(default=timezone.now, verbose_name='Date Don', blank=True, null=True)
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
    
    class Meta:
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'
        db_table = 'email_content'
    