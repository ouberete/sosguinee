from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
#router.register(r'projects', ProjectViewSet)

urlpatterns = [
   # path('api/', include(router.urls)),
    # Other API endpoint patterns...
]
