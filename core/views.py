# core/views.py
from datetime import date, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView, CreateAPIView
from .serializers import *
from .models import *
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to accept username and password, and include user info in response.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        logger.debug(f"Received payload: {attrs}")
        username = attrs.get('username')
        password = attrs.get('password')

        # Authenticate user
        user = authenticate(username=username, password=password)
        if not user:
            logger.error(f"Authentication failed for username: {username}")
            raise serializers.ValidationError({'non_field_errors': ['Unable to log in with provided credentials.']})

        if not user.is_active:
            logger.error(f"User is inactive: {username}")
            raise serializers.ValidationError({'username': ['This user account is inactive.']})

        # Generate tokens
        data = super().validate(attrs)
        return {
            "tokens": {
                "refresh": data["refresh"],
                "access": data["access"],
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role if user.role else None,
            },
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/login/  -> { tokens: { refresh, access }, user: {...} }
    """
    serializer_class = MyTokenObtainPairSerializer

class UserInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            return Driver.objects.filter(user=self.request.user)
        return Driver.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'client':
            return Client.objects.filter(user=self.request.user)
        return Client.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CarViewSet(viewsets.ModelViewSet):
    serializer_class = CarSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Car.objects.filter(driver=driver)
        return Car.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'driver':
            raise PermissionDenied("Only drivers can add cars")
        driver = Driver.objects.get(user=self.request.user)
        serializer.save(driver=driver)

class JobPostViewSet(viewsets.ModelViewSet):
    serializer_class = JobPostSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return JobPost.objects.filter(client=client)
        return JobPost.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'client':
            raise PermissionDenied("Only clients can create job posts")
        client = Client.objects.get(user=self.request.user)
        serializer.save(client=client)

class JobBidViewSet(viewsets.ModelViewSet):
    serializer_class = JobBidSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return JobBid.objects.filter(driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return JobBid.objects.filter(job_post__client=client)
        return JobBid.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'driver':
            raise PermissionDenied("Only drivers can create bids")
        driver = Driver.objects.get(user=self.request.user)
        serializer.save(driver=driver)

class JobOfferViewSet(viewsets.ModelViewSet):
    serializer_class = JobOfferSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return JobOffer.objects.filter(job_post__client=client)
        elif self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return JobOffer.objects.filter(accepted_bid__driver=driver)
        return JobOffer.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'client':
            raise PermissionDenied("Only clients can create job offers")
        client = Client.objects.get(user=self.request.user)
        job_post = serializer.validated_data.get('job_post')
        if job_post.client != client:
            raise PermissionDenied("You can only create offers for your own job posts")
        accepted_bid = serializer.validated_data.get('accepted_bid')
        if accepted_bid.job_post != job_post:
            raise PermissionDenied("The accepted bid does not belong to the job post")
        job_post.status = "job_offered"
        job_post.save()
        serializer.save()

class PublicJobPostListView(ListAPIView):
    queryset = JobPost.objects.filter(status="pending")
    serializer_class = JobPostSerializer
    permission_classes = [AllowAny]

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Payment.objects.filter(job_offer__driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return Payment.objects.filter(job_offer__job_post__client=client)
        return Payment.objects.all()

class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Rating.objects.filter(driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return Rating.objects.filter(client=client)
        return Rating.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'client':
            raise PermissionDenied("Only clients can give ratings")
        client = Client.objects.get(user=self.request.user)
        serializer.save(client=client)

class ClientDriverChatViewSet(viewsets.ModelViewSet):
    serializer_class = ClientDriverChatSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ClientDriverChat.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).select_related("chat_room", "chat_room__job_post", "chat_room__client", "chat_room__driver")

    def perform_create(self, serializer):
        user = self.request.user
        job_post = serializer.validated_data["job_post"]
        client = job_post.client
        driver = serializer.validated_data["driver"]

        if user not in [client.user, driver.user]:
            raise PermissionDenied("You can only chat if you are the job's client or a bidding driver.")

        receiver = client.user if user == driver.user else driver.user
        chat_room, created = ChatRoom.objects.get_or_create(
            job_post=job_post, client=client, driver=driver
        )

        if not created:
            raise ValidationError("A chat already exists for this job between the client and driver.")

        serializer.save(sender=user, receiver=receiver, chat_room=chat_room)

    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAuthenticated])
    def mark_as_read(self, request, pk=None):
        chat = self.get_object()
        chat.mark_as_read()
        return Response({"status": "Message marked as read."})

class CarDocViewSet(viewsets.ModelViewSet):
    serializer_class = CarDocSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return CarDoc.objects.filter(driver=driver)
        return CarDoc.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != 'driver':
            raise PermissionDenied("Only drivers can add car documents")
        driver = Driver.objects.get(user=self.request.user)
        car = serializer.validated_data.get('car')
        if car.driver != driver:
            raise PermissionDenied("You can only add documents for your own car")
        serializer.save(driver=driver)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Trip.objects.filter(job_offer__driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return Trip.objects.filter(job_offer__job_post__client=client)
        return Trip.objects.all()

    def perform_create(self, serializer):
        serializer.save()

class DemoRequestCreateAPIView(CreateAPIView):
    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    permission_classes = [permissions.AllowAny]

class RegisterView(CreateAPIView):
    """
    POST /api/auth/register/  -> { tokens: { refresh, access }, user: { id, username, role } }
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
            }
        }, status=status.HTTP_201_CREATED)