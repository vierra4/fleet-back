
from datetime import date, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication as TokenAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView  
from .serializers import *
from .models import *
from rest_framework import generics
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q
User = get_user_model()
# core/views.py

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer to allow login with either username or email.
    Expects 'identifier' (username or email) and 'password' in the request.
    """
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')

        # Try to find user by username or email
        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
        except User.DoesNotExist:
            raise serializers.ValidationError({'identifier': 'No user found with this username or email.'})

        # Authenticate user
        user = authenticate(username=user.username, password=password)
        if user is None:
            raise serializers.ValidationError({'password': 'Invalid password.'})

        # Generate tokens
        refresh = self.get_token(user)
        data = {
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role if user.role else None
            },
        }
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/  -> { tokens: { refresh, access }, user: {...} }
    """
    serializer_class = MyTokenObtainPairSerializer


class UserInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
# --- Model ViewSets with User-Specific Endpoints ---

class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # If the current user is a driver, only return his own profile.
        if self.request.user.role == 'driver':
            return Driver.objects.filter(user=self.request.user)
        return Driver.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'client':
            return Client.objects.filter(user=self.request.user)
        return Client.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CarViewSet(viewsets.ModelViewSet):
    serializer_class = CarSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # If current user is a driver, return only his cars.
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # If current user is a client, return only his job posts.
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
    authentication_classes = [TokenAuthentication]
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

# --- Updated JobOfferViewSet (created by clients) ---
class JobOfferViewSet(viewsets.ModelViewSet):
    serializer_class = JobOfferSerializer
    authentication_classes = [TokenAuthentication]
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
        # Optionally update job post status to indicate an offer has been made.
        job_post.status = "job_offered"
        job_post.save()
        serializer.save()

# --- Public endpoint to list pending job posts ---
class PublicJobPostListView(ListAPIView):
    queryset = JobPost.objects.filter(status="pending")
    serializer_class = JobPostSerializer
    permission_classes = [AllowAny]


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Show payments relevant to the current user.
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Payment.objects.filter(job_offer__driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return Payment.objects.filter(job_offer__job_post__client=client)
        return Payment.objects.all()


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # For drivers, show ratings received; for clients, show ratings they gave.
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter chats where the current user is either the sender or receiver."""
        return ClientDriverChat.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).select_related("chat_room", "chat_room__job_post", "chat_room__client", "chat_room__driver")

    def perform_create(self, serializer):
        """Automatically set the sender, enforce rules, and prevent duplicate chats."""
        user = self.request.user
        job_post = serializer.validated_data["job_post"]
        client = job_post.client
        driver = serializer.validated_data["driver"]

        if user not in [client.user, driver.user]:
            raise PermissionDenied("You can only chat if you are the job's client or a bidding driver.")

        # Ensure the receiver is correctly assigned
        receiver = client.user if user == driver.user else driver.user

        # Create or fetch the chat room for this client and driver
        chat_room, created = ChatRoom.objects.get_or_create(
            job_post=job_post, client=client, driver=driver
        )

        # Prevent duplicate chat entries for the same chat room
        if not created:
            raise ValidationError("A chat already exists for this job between the client and driver.")

        serializer.save(sender=user, receiver=receiver, chat_room=chat_room)

    @action(detail=True, methods=["POST"], permission_classes=[permissions.IsAuthenticated])
    def mark_as_read(self, request, pk=None):
        """Mark a chat message as read."""
        chat = self.get_object()
        chat.mark_as_read()
        return Response({"status": "Message marked as read."})


class CarDocViewSet(viewsets.ModelViewSet):
    serializer_class = CarDocSerializer
    authentication_classes = [TokenAuthentication]
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
        # Ensure that the provided car belongs to the current driver.
        car = serializer.validated_data.get('car')
        if car.driver != driver:
            raise PermissionDenied("You can only add documents for your own car")
        serializer.save(driver=driver)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show notifications for the current user.
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Optionally, if creation via the API is allowed.
        serializer.save(user=self.request.user)


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # For drivers: trips related to their job offers; for clients: trips for their job posts.
        if self.request.user.role == 'driver':
            driver = Driver.objects.get(user=self.request.user)
            return Trip.objects.filter(job_offer__driver=driver)
        elif self.request.user.role == 'client':
            client = Client.objects.get(user=self.request.user)
            return Trip.objects.filter(job_offer__job_post__client=client)
        return Trip.objects.all()

    def perform_create(self, serializer):
        # Depending on use case, we may enforce that only certain users can create trips.
        serializer.save()
#regisetr views point handling all roles accoridngly. 
#demo
class DemoRequestCreateAPIView(generics.CreateAPIView):
    queryset         = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    permission_classes = [permissions.AllowAny]


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/  -> { tokens: { refresh, access }, user: { id, username, role } }
    Registers a new user with a role (driver or client) and returns JWT tokens.
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