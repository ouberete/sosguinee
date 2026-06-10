<<<<<<< HEAD
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.template.loader import render_to_string
=======
import csv
import json
from types import MethodType

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.utils import timezone
>>>>>>> chore/security-design-hardening
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
<<<<<<< HEAD
)
=======
    UserActionLog,
    Report,
    EmailContent,
    UserDetails,
)
from sosguinee.utils.email_retry import resend_email_content
>>>>>>> chore/security-design-hardening

# Register your models here.
admin.site.site_header = "SOS Guinee Admin"
admin.site.site_title = "SOS Guinee Admin Portal"
admin.site.index_title = "Welcome to SOS Guinee Admin Portal"
admin.site.site_url = "https://sosguinee.com"

<<<<<<< HEAD
=======

def export_as_csv(modeladmin, request, queryset):
    model = queryset.model
    field_names = [
        field.name for field in model._meta.fields
        if not field.many_to_many and not field.one_to_many
    ]
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{model._meta.model_name}_export.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field, '') for field in field_names])
    return response


export_as_csv.short_description = "Exporter la selection en CSV"


def _record_admin_user_action(request, action, user_obj):
    UserActionLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name='User',
        object_pk=str(user_obj.pk),
        object_label=user_obj.get_username(),
        metadata={'target_user': user_obj.get_username(), 'is_active': user_obj.is_active},
        ip_address=UserActionLog.client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
    )


def resend_selected_emails(modeladmin, request, queryset):
    sent = 0
    failed = 0
    for email_content in queryset:
        try:
            sent += resend_email_content(email_content)
        except Exception as exc:
            failed += 1
            modeladmin.message_user(
                request,
                f"Email {email_content.pk} non renvoye: {exc}",
                messages.WARNING,
            )
    modeladmin.message_user(
        request,
        f"Renvoi termine: {sent} email(s) envoye(s), {failed} echec(s).",
        messages.SUCCESS if failed == 0 else messages.WARNING,
    )


resend_selected_emails.short_description = "Renvoyer les emails selectionnes"

>>>>>>> chore/security-design-hardening
@admin.register(LossAlert)
class LossAlertAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'type_alert_name', 'status_alert_name', 'region', 'prefecture', 'commune', 'quarter', 'date_alert', 'priority_badge')
    list_filter = ('loss_alert_type', 'loss_alert_status', 'region', 'prefecture', 'commune', 'quarter', 'date_alert')
    search_fields = ('name', 'description', 'public_id')
    ordering = ('-date_alert',)
    readonly_fields = ('created_at', 'public_id')
<<<<<<< HEAD
=======
    actions = [export_as_csv]
>>>>>>> chore/security-design-hardening
    
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
<<<<<<< HEAD
    readonly_fields = ('created_at', 'amount_received', 'public_id')
=======
    readonly_fields = ('created_at', 'public_id')
    actions = [export_as_csv]
>>>>>>> chore/security-design-hardening
    
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
<<<<<<< HEAD
=======
    actions = [export_as_csv]
>>>>>>> chore/security-design-hardening
    
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
<<<<<<< HEAD
=======
    actions = [export_as_csv]
>>>>>>> chore/security-design-hardening
    
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

<<<<<<< HEAD
=======

@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'model_name', 'object_label', 'ip_address')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'user__email', 'model_name', 'object_public_id', 'object_label')
    ordering = ('-created_at',)
    readonly_fields = (
        'user',
        'action',
        'model_name',
        'object_public_id',
        'object_pk',
        'object_label',
        'metadata',
        'ip_address',
        'user_agent',
        'created_at',
    )
    actions = [export_as_csv]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'reporter', 'comment_author', 'short_reason')
    list_filter = ('created_at',)
    search_fields = ('reporter__username', 'reporter__email', 'reason', 'comment__text')
    ordering = ('-created_at',)
    readonly_fields = ('comment', 'reporter', 'reason', 'created_at')
    actions = [export_as_csv]

    def comment_author(self, obj):
        return obj.comment.user if obj.comment_id else '-'
    comment_author.short_description = "Auteur commentaire"

    def short_reason(self, obj):
        return obj.reason[:90]
    short_reason.short_description = "Raison"


@admin.register(EmailContent)
class EmailContentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'subjet', 'receiver_email', 'is_sent', 'date_sent')
    list_filter = ('is_sent', 'created_at', 'date_sent')
    search_fields = ('subjet', 'receiver_email', 'plain_message', 'html_message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'date_sent')
    actions = [resend_selected_emails, export_as_csv]


@admin.register(UserDetails)
class UserDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'user_status', 'user_type', 'user_category', 'is_completed', 'created_at')
    search_fields = ('user__username', 'user__email', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'public_id')
    actions = [export_as_csv]


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = DjangoUserAdmin.list_display + ('account_status',)
    actions = ['block_users', 'unblock_users', export_as_csv]

    def account_status(self, obj):
        profile = UserDetails.objects.filter(user=obj).order_by('-created_at').first()
        return profile.user_status if profile and profile.user_status else 'Inactive'
    account_status.short_description = 'Statut compte'

    def block_users(self, request, queryset):
        count = 0
        for user_obj in queryset:
            if user_obj.is_active:
                user_obj.is_active = False
                user_obj.save(update_fields=['is_active'])
                profile, _ = UserDetails.objects.get_or_create(user=user_obj, defaults={'user_status': 'Blocked'})
                if profile.user_status != 'Blocked':
                    profile.user_status = 'Blocked'
                    profile.save(update_fields=['user_status'])
                _record_admin_user_action(request, UserActionLog.ACTION_UPDATE, user_obj)
                count += 1
        self.message_user(request, f"{count} utilisateur(s) bloque(s).", messages.SUCCESS)
    block_users.short_description = "Bloquer les utilisateurs selectionnes"

    def unblock_users(self, request, queryset):
        count = 0
        for user_obj in queryset:
            if not user_obj.is_active:
                user_obj.is_active = True
                user_obj.save(update_fields=['is_active'])
                profile, _ = UserDetails.objects.get_or_create(user=user_obj, defaults={'user_status': 'Active'})
                if profile.user_status != 'Active':
                    profile.user_status = 'Active'
                    profile.save(update_fields=['user_status'])
                _record_admin_user_action(request, UserActionLog.ACTION_UPDATE, user_obj)
                count += 1
        self.message_user(request, f"{count} utilisateur(s) debloque(s).", messages.SUCCESS)
    unblock_users.short_description = "Debloquer les utilisateurs selectionnes"

>>>>>>> chore/security-design-hardening
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

<<<<<<< HEAD
=======

def _admin_dashboard_context():
    current_year = timezone.now().year
    labels = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
    alerts_monthly = [
        LossAlert.all_objects.filter(created_at__year=current_year, created_at__month=month).count()
        for month in range(1, 13)
    ]
    funding_monthly = [
        FundingRequest.all_objects.filter(created_at__year=current_year, created_at__month=month).count()
        for month in range(1, 13)
    ]

    return {
        'total_alerts': LossAlert.objects.count(),
        'total_funding_requests': FundingRequest.objects.count(),
        'total_donations': Donation.objects.filter(status='réussi').aggregate(Sum('amount'))['amount__sum'] or 0,
        'recent_alerts': LossAlert.objects.order_by('-created_at')[:5],
        'recent_funding_requests': FundingRequest.objects.order_by('-created_at')[:5],
        'recent_donations': Donation.objects.order_by('-created_at')[:5],
        'chart_labels_json': json.dumps(labels),
        'alerts_monthly_json': json.dumps(alerts_monthly),
        'funding_monthly_json': json.dumps(funding_monthly),
    }


def _dashboard_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    extra_context.update(_admin_dashboard_context())
    return self.__class__.index(self, request, extra_context=extra_context)


admin.site.index = MethodType(_dashboard_index, admin.site)

>>>>>>> chore/security-design-hardening
