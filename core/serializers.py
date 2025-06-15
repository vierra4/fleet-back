from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()

# --- Authentication Serializers ---

ROLE_CHOICES = [
    ("driver", "Driver"),
    ("client", "Client"),
]


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # Optionally we can add asynchronous tasks here to send welcome emails.
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "role"]

# --- Model Serializers with Explicit Fields ---

class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Driver
        fields = ['user', 'license_number', 'frequent_location', 'personalID', 'created_at', 'updated_at']

class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Client
        fields = ['user', 'created_at', 'updated_at']

class CarSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Car
        fields = ['driver', 'model', 'plate_no', 'capacity', 'frequent_location', 'is_available', 'created_at', 'updated_at']

class JobPostSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = JobPost
        fields = [
            'client', 'pickup_location', 'dropoff_location', 'pickup_time',
            'title', 'description', 'status', 'created_at', 'updated_at'
        ]

class JobOfferSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = JobOffer
        fields = ['job_post', 'accepted_bid', 'car', 'start_time', 'created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Payment
        fields = ['job_offer', 'amount', 'created_at', 'updated_at']

class RatingSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['job_offer', 'rating', 'driver', 'comment', 'client', 'created_at', 'updated_at']


class ClientDriverChatSerializer(serializers.ModelSerializer):
    chat_id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ClientDriverChat
        fields = ["chat_id", "chat_room", "job_post", "driver", "client", "sender", "receiver", "message", "read_status", "created_at"]
        read_only_fields = ["chat_id", "created_at", "sender", "receiver"]

    def validate(self, data):
        """Ensure sender is either the client or the driver of the job post."""
        user = self.context["request"].user
        job_post = data["job_post"]
        client = job_post.client
        driver = data["driver"]

        if user not in [client.user, driver.user]:
            raise serializers.ValidationError("You can only chat if you are the job's client or a bidding driver.")

        return data


class CarDocSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = CarDoc
        fields = [
            'driver', 'car', 'carinsurance', 'car_license', 
            'technical_control', 'yellow_card', 'current_mileage', 
            'fuel_consumption', 'created_at', 'updated_at'
        ]

class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['user', 'message', 'is_read', 'created_at', 'updated_at']

class TripSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'job_offer', 'actual_pickup_time', 'actual_dropoff_time', 
            'distance_travelled', 'is_delivered', 'created_at', 'updated_at'
        ]
class JobBidSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = JobBid
        fields = [
            'job_post', 'driver', 'bid_message', 'proposed_price',
            'estimated_turnaround', 'status', 'created_at', 'updated_at'
        ]
#demo
class DemoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DemoRequest
        fields = [
            "id",  "email", "datetime", "message","company", "phone", "created_at"
        ]
        read_only_fields = ["id", "created_at"]