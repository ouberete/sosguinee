from django.contrib import admin
from django.urls import include, path

from page import views
from page.views import add_comment

urlpatterns = [
    path('', views.index, name='home'),
    path('funding-requests/', views.funding_request_list, name='funding_request_list'),
    path('loss-alerts/', views.loss_alert_list, name='loss_alert_list'),
    path('add-funding-request/', views.add_funding_request, name='add_funding_request'),
    path('add-loss-alert/', views.add_loss_alert, name='add_loss_alert'),
    path('contact/', views.contact, name='contact'),
    path('contact-2/', views.messageContact, name='contact-2'),
    path('loss-alert-details/<int:pk>/', views.loss_alert_detail, name='loss_alert_detail'),
    path('loss-alert-details/<uuid:public_id>/', views.loss_alert_detail, name='loss_alert_detail_public'),
    path('funding-request-details/<int:pk>/', views.funding_request_detail, name='funding_request_details'),
    path('funding-request-details/<uuid:public_id>/', views.funding_request_detail, name='funding_request_details_public'),
    path('thanks/', views.thanks, name='thanks'),
    path('donation/', views.donation, name='donation'),
    path('merci/', views.donation_thanks, name='donation_thanks'),
    path('confirmation-loss_alert-added/', views.confirmation_loss_alert_added, name='confirmation_loss_alert_added'),
    path('confirmation-funding_request-added/', views.confirmation_funding_request_added, name='confirmation_funding_request_added'),
    path('help-support/', views.help_support, name='help_support'),
    path('policy-privacy/', views.policy_privacy, name='policy_privacy'),
    path('about-us', views.about, name='about_us'),
    path('api/', include('page.api_urls')),
    path('funding/<int:pk>/paycard/', views.paycard_funding, name='paycard_funding'),
    path('funding/<uuid:public_id>/paycard/', views.paycard_funding, name='paycard_funding_public'),
    path('paycard_funding_payment/<int:funding_id>/paycard/', views.start_paycard_funding_payment, name='funding_paycard_payment'),
    path('paycard_funding_payment/<uuid:funding_public_id>/paycard/', views.start_paycard_funding_payment, name='funding_paycard_payment_public'),
    path('paycard/callback/<int:payment_id>/<str:type>/', views.paycard_payment_callback, name='paycard_payment_callback'),
    path('paycard/callback/<uuid:payment_public_id>/<str:type>/', views.paycard_payment_callback, name='paycard_payment_callback_public'),
    #path('comment/<str:model_name>/<int:object_id>/add/', add_comment, name='add_comment'),
    path('comment/add/<str:model_name>/<int:object_id>/', views.add_comment, name='add_comment'),
    path('comment/add/<str:model_name>/<uuid:payment_public_id>/', views.add_comment, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/edit/<uuid:payment_public_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comment/delete/<uuid:payment_public_id>/', views.delete_comment, name='delete_comment'),
    path('comment/report/<int:comment_id>/', views.report_comment, name='report_comment'),
    path('comment/report/<uuid:payment_public_id>/', views.report_comment, name='report_comment'),

]
