from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # We won't use Django admin as per requirements
    # path('admin/', admin.site.urls),
    
    # Include all app URLs with the required prefix
    path('webapps2025/', include('register.urls')),
    path('webapps2025/', include('payapp.urls')),
]