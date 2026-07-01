from django.contrib import admin
from .models import DjomyPayment


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

    def has_add_permission(self, request):
        # Les paiements ne doivent être créés que par le service/webhook
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
