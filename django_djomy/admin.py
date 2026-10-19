from django.contrib import admin, messages
from .models import DjomyPayment
from .services import DjomyService


def check_djomy_payment_gateway_status(modeladmin, request, queryset):
    service = DjomyService()
    updated_count = 0
    for payment in queryset:
        candidate = payment.transaction_id or payment.merchant_reference
        if not candidate:
            continue
        data = service.get_payment_status(candidate)
        if isinstance(data, dict):
            raw_status = (
                data.get("status")
                or data.get("payment_status")
                or data.get("transaction_status")
                or data.get("state")
            )
            if raw_status:
                s = str(raw_status).upper()
                if s in {"SUCCESS", "SUCCEEDED", "PAID", "COMPLETED", "RÉUSSI"}:
                    payment.status = "SUCCESS"
                elif s in {"FAILED", "FAILURE", "ERROR", "ÉCHOUÉ"}:
                    payment.status = "FAILED"
                elif s in {"CANCELLED", "CANCELED", "ANNULÉ"}:
                    payment.status = "CANCELLED"
                payment.raw_payload = data
                payment.save(update_fields=["status", "raw_payload", "updated_at"])
                updated_count += 1
    modeladmin.message_user(
        request,
        f"{updated_count} paiement(s) Djomy synchronisé(s) depuis l'API.",
        messages.SUCCESS if updated_count > 0 else messages.INFO,
    )


check_djomy_payment_gateway_status.short_description = "Vérifier le statut auprès de l'API Djomy"


@admin.register(DjomyPayment)
class DjomyPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'merchant_reference',
        'amount',
        'currency',
        'status',
        'phone',
        'transaction_id',
        'created_at',
    )
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('merchant_reference', 'transaction_id', 'phone')
    readonly_fields = ('raw_payload', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = [check_djomy_payment_gateway_status]

    def has_add_permission(self, request):
        # Les paiements ne doivent être créés que par le service/webhook
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
