from django.urls import path, include
from apps.banks_app.otp import urls as otp_urls


app_name = 'soap'
urlpatterns = [
    path('otp/', include(otp_urls)),
]
