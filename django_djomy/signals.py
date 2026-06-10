import django.dispatch

# Signal envoyé lorsqu'un paiement Djomy est validé avec succès
# Arguments fournis :
# - sender: La classe émettrice
# - reference: La référence marchande du paiement (str)
# - transaction_id: L'ID de transaction Djomy (str)
# - amount: Le montant payé
djomy_payment_success = django.dispatch.Signal()
