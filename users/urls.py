from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ScheduleViewSet,
    JobViewSet,
    register,
    CustomTokenObtainPairView,
    complete_profile,
    JobScraperViewSet
)

from rest_framework_simplejwt.views import TokenRefreshView


router = DefaultRouter()
router.register(r'schedule', ScheduleViewSet, basename='schedule')
router.register(r'jobs', JobViewSet, basename='jobs')

router.register(r'scraper/jobs', JobScraperViewSet, basename='scraper-jobs')

urlpatterns = [
    # 🔐 AUTHENTIFICATION
    path('register/', register),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('complete-profile/', complete_profile),

    # 📅 API (schedule + jobs)
    path('', include(router.urls)),
]