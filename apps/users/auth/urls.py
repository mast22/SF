from django.urls import path

from . import views as v


app_name = 'users'
urlpatterns = [
    # URLs that do not require a session or valid token
    path('refresh-token/', v.TokenRefreshView.as_view(), name='refresh_token'),
    path('login/', v.LoginView.as_view(), name='login'),
    path('logout/', v.LogoutView.as_view(), name='logout'),
    path('login/confirm-code/', v.LoginConfirmCodeView.as_view(), name='login_confirm_code'),
    path('password-reset/', v.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm-code/', v.PasswordResetConfirmCodeView.as_view(), name='password_reset_confirm_code'),
    path('password-reset/set-password/', v.PasswordResetSetPasswordView.as_view(), name='password_reset_set_password'),
]
