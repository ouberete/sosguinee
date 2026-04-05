from django.contrib import admin
from .models.subscription import SubscriptionPlan, UserSubscription, SubscriptionPayment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_id', 'price', 'duration_days', 'created_at')
    search_fields = ('name', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    ordering = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'public_id', 'plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('public_id', 'user__username', 'plan__name')
    list_filter = ('is_active', 'plan')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    ordering = ('-start_date',)

@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'user', 'plan', 'amount', 'status', 'payment_date')
    search_fields = ('public_id', 'transaction_id', 'user__username', 'plan__name')
    list_filter = ('status',)
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    ordering = ('-payment_date',)
