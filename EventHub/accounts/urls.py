from django.urls import path
from events.views import (
    register, login_view, logout_view, verify_signup_email,
    forgot_password, verify_otp, reset_password
)

urlpatterns = [
    path('register/', register, name='register'),
    path('verify-signup/', verify_signup_email, name='verify_signup_email'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
]