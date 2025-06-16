from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.db.models import Q, F
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import datetime
#from dateutil.relativedelta import relativedelta

# Base model for automatic timestamping.
class Timer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Define role choices for the custom user.
ROLE_CHOICES = [
    ("driver", "Driver"),
    ("client", "Client"),
]

# Custom user model.
class CustomUser(AbstractUser):
    phone = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_driver = models.BooleanField(default=False)
    email = models.EmailField(unique=True)  # Add unique=True

    def __str__(self):
        return self.username

class Driver(Timer):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    license_number = models.CharField(max_length=100)
    frequent_location = models.CharField(max_length=100, blank=True, null=True)
    personalID = models.ImageField(upload_to="ID")
    
    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['-created_at']

class Client(Timer):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    
    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['-created_at']

class Car(Timer):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    plate_no = models.CharField(max_length=100)
    capacity = models.CharField(max_length=100)
    frequent_location = models.CharField(max_length=200, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.model

    class Meta:
        ordering = ['-created_at']
        unique_together = ['driver', 'plate_no']

class JobPost(Timer):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("job_offered", "Job Offered"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("in_progress", "In Progress"),
        ("on_hold", "On Hold"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    pickup_location = models.CharField(max_length=100)
    dropoff_location = models.CharField(max_length=100)
    pickup_time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        unique_together = ['client', 'title']


class JobBid(Timer):
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='bids')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    bid_message = models.TextField()
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_turnaround = models.DurationField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Bid by {self.driver.user.username} on {self.job_post.title}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ('job_post', 'driver')


class JobOffer(Timer):
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    accepted_bid = models.OneToOneField(JobBid, on_delete=models.CASCADE, related_name='job_offer')
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Offer to {self.accepted_bid.driver.user.username} for {self.job_post.title}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['job_post', 'accepted_bid']

class Payment(Timer):
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.job_offer.driver.user.username} - {self.job_offer.job_post.title}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['job_offer', 'amount']

class Rating(Timer):
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE)
    rating = models.IntegerField()
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200, blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Rating: {self.rating}"


class ChatRoom(Timer):
    """Represents a chat room for a specific job, between a client and a driver."""
    chat_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="chat_rooms")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="chat_rooms")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="chat_rooms")

    class Meta:
        unique_together = ("job_post", "client", "driver")
    
    def __str__(self):
        return f"Chat Room for Job: {self.job_post.title} | {self.client.user.username} ↔ {self.driver.user.username}"


class ClientDriverChat(Timer):
    """Represents a chat message between the client and driver within a chat room."""
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name="received_messages", on_delete=models.CASCADE)
    message = models.TextField()
    read_status = models.BooleanField(default=False)

    def clean(self):
        """Ensure the sender and receiver are either the client or the bidding driver."""
        if self.sender not in [self.chat_room.client.user, self.chat_room.driver.user]:
            raise ValidationError("Sender must be either the job's client or the bidding driver.")
        if self.receiver not in [self.chat_room.client.user, self.chat_room.driver.user]:
            raise ValidationError("Receiver must be either the job's client or the bidding driver.")
        if self.sender == self.receiver:
            raise ValidationError("Sender and receiver cannot be the same user.")

    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)

    def mark_as_read(self):
        """Mark the chat message as read."""
        self.read_status = True
        self.save(update_fields=["read_status"])

    def get_unread_messages_count(self):
        """Get the count of unread messages for the receiver."""
        return ClientDriverChat.objects.filter(receiver=self.receiver, read_status=False).count()

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} in Chat {self.chat_room.chat_id}"


class CarDoc(Timer):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    carinsurance = models.FileField(upload_to="insurance")
    car_license = models.FileField(upload_to="license")
    technical_control = models.FileField(upload_to="technical_control")
    yellow_card = models.FileField(upload_to="yellow_card")
    current_mileage = models.IntegerField()
    fuel_consumption = models.IntegerField()
    
    def __str__(self):
        return f"{self.driver.user.username} - {self.car.model}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['driver', 'car']

    def update_car_docs(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.save()

    def delete_car_docs(self):
        self.delete()

    def get_car_docs(self):
        return {
            "insurance": self.carinsurance.url if self.carinsurance else None,
            "license": self.car_license.url if self.car_license else None,
            "technical_control": self.technical_control.url if self.technical_control else None,
            "yellow_card": self.yellow_card.url if self.yellow_card else None,
        }

# Additional models
class Notification(Timer):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"

class Trip(Timer):
    job_offer = models.OneToOneField(JobOffer, on_delete=models.CASCADE)
    actual_pickup_time = models.DateTimeField(null=True, blank=True)
    actual_dropoff_time = models.DateTimeField(null=True, blank=True)
    distance_travelled = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_delivered=models.BooleanField(default=False)
    def __str__(self):
        return f"Trip: {self.job_offer.job_post.title}"
class DemoRequest(models.Model):
    full_name   = models.CharField(max_length=150)
    email       = models.EmailField()
    company     = models.CharField(max_length=150, blank=True)
    phone       = models.CharField(max_length=20, blank=True)
    datetime    = models.DateTimeField(null=True, blank=True)
    message     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} <{self.email}> @ {self.created_at:%Y-%m-%d %H:%M}"


