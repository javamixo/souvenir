from django.urls import path, include
from shop import views  # Import your shop app's views
from django.contrib import admin # Add this line

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shop/', include('shop.urls')),
    path('', views.dashboard, name='home'),  # Add this line
]

