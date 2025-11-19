from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.template.loader import render_to_string
from .models import (
    LossAlertType,
    LossAlert,
    FundingType,
    LossAlertStatus,
    FundingRequestStatus,
    FundingRequest,
    Donation,
    FundPayment,
    MessageContact,
    Comment,
    Region,
    Prefecture,
    Commune,
    Quarter,
)

# Register your models here.
admin.site.site_header = "SOS Guinee Admin"
admin.site.site_title = "SOS Guinee Admin Portal"
admin.site.index_title = "Welcome to SOS Guinee Admin Portal"
admin.site.site_url = "https://sosguinee.com"

@admin.register(LossAlert)
class LossAlertAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'type_alert_name', 'status_alert_name', 'region', 'prefecture', 'commune', 'quarter', 'date_alert', 'priority_badge')
    list_filter = ('loss_alert_type', 'loss_alert_status', 'region', 'prefecture', 'commune', 'quarter', 'date_alert')
    search_fields = ('name', 'description', 'public_id')
    ordering = ('-date_alert',)
    readonly_fields = ('created_at', 'public_id')
    
    def type_alert_name(self, obj):
        return obj.loss_alert_type.name if obj.loss_alert_type else '-'
    type_alert_name.short_description = 'Type d\'alerte'
    
    def status_alert_name(self, obj):
        return obj.loss_alert_status.name if obj.loss_alert_status else '-'
    status_alert_name.short_description = 'Statut'
    
    def priority_badge(self, obj):
        # Some deployments might not have a 'priority' field on LossAlert
        priority = getattr(obj, 'priority', None)
        if not priority:
            return '-'
        colors = {
            'Haute': 'red',
            'Moyenne': 'orange',
            'Basse': 'green'
        }
        color = colors.get(priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 7px; border-radius: 3px;">{}</span>',
            color,
            priority
        )
    priority_badge.short_description = 'Priorité'

@admin.register(FundingRequest)
class FundingRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'public_id', 'beneficiary_name', 'funding_request_status_name', 'region', 'prefecture', 'commune', 'quarter', 'funding_amount', 'progress_bar', 'days_remaining')
    list_filter = ('funding_request_type', 'funding_request_status', 'region', 'prefecture', 'commune', 'quarter', 'created_at')
    search_fields = ('title', 'beneficiary_name', 'description_needs', 'public_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'amount_received', 'public_id')
    
    def funding_request_status_name(self, obj):
        return obj.funding_request_status.name if obj.funding_request_status else '-'
    funding_request_status_name.short_description = 'Statut'
    
    def progress_bar(self, obj):
        progress = obj.progress
        return format_html(
            '''
            <div style="width: 100px; background-color: #f0f0f0; height: 20px; border-radius: 10px;">
                <div style="width: {}%; background-color: #4CAF50; height: 100%; border-radius: 10px;">
                    <span style="padding: 0 5px; color: white;">{}%</span>
                </div>
            </div>
            ''',
            min(progress, 100),
            progress
        )
    progress_bar.short_description = 'Progression'

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'donor_name', 'amount', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('public_id', 'donor_first_name', 'donor_last_name', 'donor_email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'transaction_id', 'public_id')
    
    def donor_name(self, obj):
        return f"{obj.donor_first_name} {obj.donor_last_name}"
    donor_name.short_description = "Donateur"

@admin.register(FundPayment)
class FundPaymentAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'funding_request_link', 'donor_name', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('public_id', 'donor_first_name', 'donor_last_name', 'funding_request__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'transaction_id', 'public_id')
    
    def funding_request_link(self, obj):
        url = reverse('admin:page_fundingrequest_change', args=[obj.funding_request.id])
        return format_html('<a href="{}">{}</a>', url, obj.funding_request.title)
    funding_request_link.short_description = "Demande de financement"
    
    def donor_name(self, obj):
        return f"{obj.donor_first_name} {obj.donor_last_name}"
    donor_name.short_description = "Donateur"

@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'name', 'email', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('public_id', 'name', 'email', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'public_id')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Marquer comme non lu"

# Enregistrement des autres modèles avec des configurations simples
@admin.register(LossAlertType)
class LossAlertTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'created_at')
    search_fields = ('name', 'public_id', 'description')
    ordering = ('name',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')


@admin.register(FundingType)
class FundingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'created_at')
    search_fields = ('name', 'public_id', 'description')
    ordering = ('name',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')


@admin.register(LossAlertStatus)
class LossAlertStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'created_at')
    search_fields = ('name', 'public_id', 'description')
    ordering = ('name',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')


@admin.register(FundingRequestStatus)
class FundingRequestStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'created_at')
    search_fields = ('name', 'public_id', 'description')
    ordering = ('name',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(Prefecture)
class PrefectureAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'public_id', 'created_at')
    list_filter = ('region',)
    search_fields = ('name', 'region__name')
    ordering = ('region__name', 'name')
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefecture', 'public_id', 'created_at')
    list_filter = ('prefecture',)
    search_fields = ('name', 'prefecture__name', 'prefecture__region__name')
    ordering = ('prefecture__name', 'name')
    readonly_fields = ('public_id', 'created_at', 'updated_at')

@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ('name', 'commune', 'public_id', 'created_at')
    list_filter = ('commune',)
    search_fields = ('name', 'commune__name', 'commune__prefecture__name', 'commune__prefecture__region__name')
    ordering = ('commune__name', 'name')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'public_id', 'user', 'created_at')
    search_fields = ('public_id', 'text', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')

# Personnalisation du tableau de bord admin
class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Personnalisation de l'ordre des applications
        return app_list
    
    def index(self, request, extra_context=None):
        # Statistiques pour le tableau de bord
        total_alerts = LossAlert.objects.count()
        total_funding_requests = FundingRequest.objects.count()
        total_donations = Donation.objects.filter(status='réussi').aggregate(Sum('amount'))['amount__sum'] or 0
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_alerts': total_alerts,
            'total_funding_requests': total_funding_requests,
            'total_donations': total_donations,
            'recent_alerts': LossAlert.objects.order_by('-created_at')[:5],
            'recent_funding_requests': FundingRequest.objects.order_by('-created_at')[:5],
            'recent_donations': Donation.objects.filter(status='réussi').order_by('-created_at')[:5],
        })
        
        return super().index(request, extra_context)

