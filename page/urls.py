from django.contrib import admin
from django.urls import path

from page import views

urlpatterns = [
    path('', views.index, name='home'),
    path('funding-requests/', views.funding_request_list, name='funding_request_list'),
    path('loss-alerts/', views.loss_alert_list, name='loss_alert_list'),
    path('add-funding-request/', views.add_funding_request, name='add_funding_request'),
    path('add-loss-alert/', views.add_loss_alert, name='add_loss_alert'),
    path('contact/', views.contact, name='contact'),
    path('loss-alert-detail/<int:pk>/', views.loss_alert_detail, name='loss_alert_detail'),
    path('funding-request-detail/<int:pk>/', views.funding_request_detail, name='funding_request_detail'),
    path('thanks/', views.thanks, name='thanks'),
    path('donation/', views.donation, name='donation'),
]
