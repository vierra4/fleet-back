from django.test import TestCase

# Create your tests here.
#signup
{
  "username": "testuser",
  "email": "test@example.com",
  "phone": "1234567890",
  "role": "driver",  // or "client"
  "password": "StrongPassword123"
}
#login
{
  "username": "testuser",
  "password": "StrongPassword123"
}
#User Info
#logout
#driver
license_number: "LIC1234"

frequent_location: "City Center"

personalID: (upload a file)
#cars
{
  "model": "Toyota Prius",
  "plate_no": "ABC123",
  "capacity": "4",
  "frequent_location": "Downtown",
  "is_available": true
}
#jobpost
{
  "pickup_location": "Location A",
  "dropoff_location": "Location B",
  "title": "Deliver my package",
  "description": "Need a reliable driver",
  "status": "pending"  // optional, since it defaults to "pending"
}
#joboffer
{
  "job_post": 3,
  "car": 5
}
#payment
{
  "job_offer": 4,
  "amount": "15.00"
}
#ratings/client
{
  "job_offer": 4,
  "rating": 5,
  "driver": 1,
  "comment": "Excellent service!"
}
#chats
{
  "job_post": 3,
  "driver": 1,
  "client": 2,
  "receiver": 2,
  "message": "Hello, I have a question about your job post."
}
#cardocument
car: Car ID (5)
carinsurance: (file upload)
car_license: (file upload)
technical_control: (file upload)
yellow_card: (file upload)
current_mileage: 10000
fuel_consumption: 8
#notify
{
  "message": "Your job has been updated."
}
#trips
{
  "job_offer": 4,
  "actual_pickup_time": "2025-03-23T10:00:00Z",
  "actual_dropoff_time": "2025-03-23T10:30:00Z",
  "distance_travelled": "12.50",
  "is_delivered": true
}

