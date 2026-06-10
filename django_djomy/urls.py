from django.urls import path
from .views import djomy_webhook, admin_liste_paiements, detail_transaction_check

app_name = 'django_djomy'

urlpatterns = [
    path('webhooks/djomy/', djomy_webhook, name='djomy_webhook'),
    path('admin/djomy/list/', admin_liste_paiements, name='admin_liste_paiements'),
    path('admin/djomy/check/<str:transaction_id>/', detail_transaction_check, name='detail_transaction_check'),
]
