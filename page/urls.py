from django.urls import include, path

from page import views

urlpatterns = [
    path('', views.index, name='home'),
    path('funding-requests/', views.funding_request_list, name='funding_request_list'),
    path('loss-alerts/', views.loss_alert_list, name='loss_alert_list'),
    path('add-funding-request/', views.add_funding_request, name='add_funding_request'),
    path('edit-funding-request/<uuid:public_id>/', views.edit_funding_request, name='edit_funding_request'),
    path('delete-funding-request/<uuid:public_id>/', views.delete_funding_request, name='delete_funding_request'),
    path('add-loss-alert/', views.add_loss_alert, name='add_loss_alert'),
    path('edit-loss-alert/<uuid:public_id>/', views.edit_loss_alert, name='edit_loss_alert'),
    path('delete-loss-alert/<uuid:public_id>/', views.delete_loss_alert, name='delete_loss_alert'),
    path('contact/', views.contact, name='contact'),
    path('loss-alert-details/<int:pk>/', views.loss_alert_detail, name='loss_alert_detail'),
    path('loss-alert-details/<uuid:public_id>/', views.loss_alert_detail, name='loss_alert_detail_public'),
    path('funding-request-details/<int:pk>/', views.funding_request_detail, name='funding_request_details'),
    path('funding-request-details/<uuid:public_id>/', views.funding_request_detail, name='funding_request_details_public'),
    path('thanks/', views.thanks, name='thanks'),
    path('donation/', views.donation, name='donation'),
    path('merci/', views.donation_thanks, name='donation_thanks'),
    path('confirmation-loss-alert-added/', views.confirmation_loss_alert_added, name='confirmation_loss_alert_added'),
    path('confirmation-funding-request-added/', views.confirmation_funding_request_added, name='confirmation_funding_request_added'),
    path('help-support/', views.help_support, name='help_support'),
    path('policy-privacy/', views.policy_privacy, name='policy_privacy'),
    path('about-us', views.about, name='about_us'),
    path('api/', include('page.api_urls')),
    path('funding/<int:pk>/djomy/', views.djomy_funding, name='djomy_funding'),
    path('funding/<uuid:public_id>/djomy/', views.djomy_funding, name='djomy_funding_public'),
    path('djomy_funding_payment/<int:funding_id>/djomy/', views.start_djomy_funding_payment, name='funding_djomy_payment'),
    path('djomy_funding_payment/<uuid:funding_public_id>/djomy/', views.start_djomy_funding_payment, name='funding_djomy_payment_public'),
    path('djomy/callback/<int:payment_id>/<str:type>/', views.djomy_payment_callback, name='djomy_payment_callback'),
    path('djomy/callback/<uuid:payment_public_id>/<str:type>/', views.djomy_payment_callback, name='djomy_payment_callback_public'),
    path('comment/add/<str:model_name>/<int:object_id>/', views.add_comment, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comment/report/<int:comment_id>/', views.report_comment, name='report_comment'),

    # Aliases to match JS endpoints used by static/js/comments.js
    path('comments/<int:comment_id>/edit/', views.edit_comment, name='js_edit_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='js_delete_comment'),
    path('comments/<int:comment_id>/report/', views.report_comment, name='js_report_comment'),

    # Close/resolve endpoints
    path('funding-request/<uuid:public_id>/close/', views.close_funding_request, name='close_funding_request'),
    path('loss-alert/<uuid:public_id>/close/', views.close_loss_alert, name='close_loss_alert'),

]
