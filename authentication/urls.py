from django.urls import path
from .views import RegisterView, VerifyEmail

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', VerifyEmail.as_view(), name='activate'),
]
