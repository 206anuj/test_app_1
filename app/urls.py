from django.urls import path
from . import views

urlpatterns = [
    path('sync-salesforce/', views.sync_salesforce_data, name='sync_salesforce'),
    path('trigger-sync/', views.trigger_sync, name='trigger_sync'),
]