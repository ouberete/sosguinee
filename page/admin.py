from django.contrib import admin
from .models import (
    LossAlertType,
    LossAlert,
    FundingType,
    LossAlertStatus,
    FundingRequestStatus,
)
# Register your models here.
admin.site.site_header = "SOS Guinee Admin"
admin.site.site_title = "SOS Guinee Admin Portal"
admin.site.index_title = "Welcome to SOS Guinee Admin Portal"
admin.site.site_url = "https://sosguinee.com"
admin.site.register(LossAlertType)
admin.site.register(LossAlert)
admin.site.register(FundingType)
admin.site.register(LossAlertStatus)
admin.site.register(FundingRequestStatus)