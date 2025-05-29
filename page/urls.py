from django.contrib import admin
from django.urls import include, path

from page import views

urlpatterns = [
    path('', views.index, name='home'),
    path('funding-requests/', views.funding_request_list, name='funding_request_list'),
    path('loss-alerts/', views.loss_alert_list, name='loss_alert_list'),
    path('add-funding-request/', views.add_funding_request, name='add_funding_request'),
    path('add-loss-alert/', views.add_loss_alert, name='add_loss_alert'),
    path('contact/', views.contact, name='contact'),
    path('contact-2/', views.messageContact, name='contact-2'),
    path('loss-alert-details/<int:pk>/', views.loss_alert_detail, name='loss_alert_detail'),
    path('funding-request-details/<int:pk>/', views.funding_request_detail, name='funding_request_details'),
    path('thanks/', views.thanks, name='thanks'),
    path('donation/', views.donation, name='donation'),
    path('merci/', views.donation_thanks, name='donation_thanks'),
    path('confirmation-loss_alert-added/', views.confirmation_loss_alert_added, name='confirmation_loss_alert_added'),
    path('confirmation-funding_request-added/', views.confirmation_funding_request_added, name='confirmation_funding_request_added'),
    path('help-support/', views.help_support, name='help_support'),
    path('policy-privacy/', views.policy_privacy, name='policy_privacy'),
    path('about-us', views.about, name='about_us'),
    path('api/', include('page.api_urls')),
]
