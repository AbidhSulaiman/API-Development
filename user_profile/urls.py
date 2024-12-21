
from django.urls import path, include
from .views import upload_user_details

urlpatterns = [
    path('add_user/', upload_user_details, name = 'add_user')
]
