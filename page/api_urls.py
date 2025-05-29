from django.contrib import admin
from django.urls import path

from page import views

urlpatterns = [
    path('funding-requests/', views.FundingRequestListView.as_view(), name='funding_request_list_api'),
    path('loss-alerts/', views.LossAlertListView.as_view(), name='loss_alert_list_api'),
]
