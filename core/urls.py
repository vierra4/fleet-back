from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'cars', CarViewSet, basename='car')
router.register(r'jobposts', JobPostViewSet, basename='jobpost')
router.register(r'joboffers', JobOfferViewSet, basename='joboffer')
router.register(r'jobbids', JobBidViewSet, basename='jobbids')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'chats', ClientDriverChatViewSet, basename='clientdriverchat')#
router.register(r'cardocs', CarDocViewSet, basename='cardoc')
router.register(r'notifications', NotificationViewSet, basename='notification')#
router.register(r'trips', TripViewSet, basename='trip')

urlpatterns = [
    # Authentication endpoints
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/', UserInfoView.as_view(), name='user-info'),
    # Public endpoint for pending job posts
    path('public/jobposts/', PublicJobPostListView.as_view(), name='public-jobposts'),
    path("book-demo/", DemoRequestCreateAPIView.as_view(), name="book-demo"),
    # Model endpoints
]
