from django.contrib import admin
from django.urls import path

from page import views

urlpatterns = [
    path('funding-requests/', views.FundingRequestListView.as_view(), name='funding_request_list_api'),
    path('loss-alerts/', views.LossAlertListView.as_view(), name='loss_alert_list_api'),
    # Cascading location endpoints
    path('locations/prefectures/', views.prefectures_by_region, name='prefectures_by_region'),
    path('locations/communes/', views.communes_by_prefecture, name='communes_by_prefecture'),
    path('locations/quarters/', views.quarters_by_commune, name='quarters_by_commune'),
]
