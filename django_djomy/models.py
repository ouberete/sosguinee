from django.db import models
from django.utils.translation import gettext_lazy as _

class DjomyPayment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('SUCCESS', 'Réussi'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
    )

    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name=_("ID Transaction Djomy"))
    merchant_reference = models.CharField(max_length=255, db_index=True, verbose_name=_("Référence Marchand"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Montant"))
    currency = models.CharField(max_length=10, default="GNF", verbose_name=_("Devise"))
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Téléphone"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name=_("Statut"))
    payment_url = models.URLField(max_length=500, null=True, blank=True, verbose_name=_("URL de Paiement"))
    
    raw_payload = models.JSONField(null=True, blank=True, verbose_name=_("Payload Webhook"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Paiement Djomy")
        verbose_name_plural = _("Paiements Djomy")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.merchant_reference} - {self.amount} {self.currency} ({self.status})"
