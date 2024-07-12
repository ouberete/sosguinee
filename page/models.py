from django.db import models
from django.contrib.auth.models import User

class BaseEntity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

Gender = (
    ('Male', 'Masculin'),
    ('Female', 'Feminin'),
)

class FundingType(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class LostType(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()

class LostStatus(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()

class FundingRequestStatus(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

UserStatus = (
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Blocked', 'Blocked'),
)

class UserDetails(BaseEntity):
    name = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=255, null=True, blank=True)
    telephone = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=Gender)
    user_status = models.CharField(max_length=255, choices=UserStatus, default='Inactive')

class OptionalAlertImage(BaseEntity):
    image = models.ImageField(upload_to='img/alerts/')

class LossAlert(BaseEntity):
    name = models.CharField(max_length=255)
    loss_alert_type = models.ForeignKey(LostType, on_delete=models.PROTECT, blank=True, null=True)
    loss_alert_status = models.ForeignKey(LostStatus, on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField()
    principal_image = models.ImageField(upload_to='img/alerts/')
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255)
    country = models.CharField(max_length=255, default="Guinée", blank=True, null=True)
    city = models.CharField(max_length=255)
    quarter = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    date_alert = models.DateField()
    hour_alert = models.TimeField(blank=True, null=True)
    optional_images = models.ManyToManyField(OptionalAlertImage, blank=True)

    def add_images(self, images):
        for image in images:
            img = OptionalAlertImage(image=image)
            img.save()
            self.optional_images.add(img)

class OptionalImageFunding(BaseEntity):
    image = models.ImageField(upload_to='img/Fundings/')

class FundingRequest(BaseEntity):
    beneficiary_name = models.CharField(max_length=255)
    funding_amount = models.DecimalField(max_digits=10, decimal_places=2)
    funding_request_status = models.ForeignKey(FundingRequestStatus, on_delete=models.PROTECT, blank=True, null=True)
    funding_request_type = models.ForeignKey(FundingType, on_delete=models.PROTECT, blank=True, null=True)
    description_needs = models.TextField()
    principal_image = models.ImageField(upload_to='img/Fundings/')
    optional_images = models.ManyToManyField(OptionalImageFunding, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255)
    country = models.CharField(max_length=255, default="Guinée", blank=True, null=True)
    city = models.CharField(max_length=255)
    quarter = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def add_images(self, images):
        for image in images:
            img = OptionalImageFunding(image=image)
            img.save()
            self.optional_images.add(img)
