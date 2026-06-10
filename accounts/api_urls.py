from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import subscription_views

router = DefaultRouter()

urlpatterns = [
    path('api/', include(router.urls)),
    path('subscription/plans/', subscription_views.subscription_plans, name='subscription_plans'),
    path('subscription/subscribe/', subscription_views.subscribe, name='subscribe'),
    path('subscription/cancel/', subscription_views.cancel_subscription, name='cancel_subscription'),
    path('subscription/status/', subscription_views.subscription_status, name='subscription_status'),
]
