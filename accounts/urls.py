
from django.contrib import admin
from django.urls import path, include

from accounts.forms import UserDocumentForm, UserInfosForm, UserLinkForm
from . import views
from .views import FORMS

urlpatterns = [
    path(r'login', views.signin, name="login"),
    path(r'register', views.register, name="register"),
    path(r'reset-password', views.reset_password, name="reset-password"),
    path(r'change-password', views.change_password, name="change_password"),
    path(r'logout', views.user_logout, name="logout"),
    path(r'profile', views.user_profile, name="profile"),
    path(r'update-profile', views.UpdateUserProfileWizard.as_view(FORMS), name="update_profile"),
    path(r'account-created', views.acount_created, name="account-created"),
    path(r'activate/<uidb64>/<token>', views.activate, name="activate"),
    path(r'user-infos', views.UserInfosView.as_view(), name="user-infos"),
    path(r'user-documents', views.UserDocumentView.as_view(), name="user-documents"),
    path(r'user-link', views.UserLinkView.as_view(), name="user-link"),
    path(r'otp-login/', views.otp_login_view, name='otp_login'),
]