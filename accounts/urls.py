from django.urls import path

from . import views
from .views.subscription_views import (
    subscription_plans,
    subscribe,
    cancel_subscription,
    subscription_status,
    plan_detail_by_public_id,
    payment_detail_by_public_id,
)

urlpatterns = [
    path(r'login', views.signin, name="login"),
    path(r'register', views.register, name="register"),
    path(r'resend-activation', views.resend_activation, name="resend_activation"),
    path(r'reset-password', views.reset_password, name="reset-password"),
    path(r'change-password', views.change_password, name="change_password"),
    path(r'logout', views.user_logout, name="logout"),
    path(r'profile', views.user_profile, name="profile"),
    path(r'update-profile', views.UpdateUserProfileWizard.as_view(views.FORMS), name="update_profile"),
    path(r'account-created', views.acount_created, name="account-created"),
    path(r'activate/<uidb64>/<token>', views.activate, name="activate"),
    path(r'user-infos', views.UserInfosView.as_view(), name="user-infos"),
    path(r'user-documents', views.UserDocumentView.as_view(), name="user-documents"),
    path(r'user-link', views.UserLinkView.as_view(), name="user-link"),

    # URLs d'abonnement
    path('subscriptions/plans/', subscription_plans, name='subscription_plans'),
    path('subscriptions/subscribe/', subscribe, name='subscribe'),
    path('subscriptions/cancel/', cancel_subscription, name='cancel_subscription'),
    path('subscriptions/status/', subscription_status, name='subscription_status'),
    # API (lecture par UUID)
    path('api/subscriptions/plans/<uuid:public_id>/', plan_detail_by_public_id, name='subscription_plan_detail_by_public_id'),
    path('api/subscriptions/payments/<uuid:public_id>/', payment_detail_by_public_id, name='subscription_payment_detail_by_public_id'),
]
