from .subscription_views import subscription_plans, subscribe, cancel_subscription, subscription_status
<<<<<<< HEAD
from .auth_views import signin, register, activate, user_logout, acount_created, reset_password, change_password, otp_login_view
=======
from .auth_views import signin, register, activate, resend_activation, user_logout, acount_created, reset_password, change_password, otp_login_view
>>>>>>> chore/security-design-hardening
from .profile import (user_profile, UpdateUserProfileWizard, UserInfosView, UserDocumentView, UserLinkView, FORMS)
