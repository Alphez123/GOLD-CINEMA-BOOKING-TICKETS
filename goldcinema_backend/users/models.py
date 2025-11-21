from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import random
import string

def generate_user_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class CustomUser(AbstractUser):
    customer_id = models.CharField(max_length=10, unique=True, default=generate_user_id)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.CharField(max_length=50)
    seats = models.CharField(max_length=200)  # Example: "A1, A2, A3"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.movie_name} ({self.date} {self.time})"

class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100, blank=True, null=True)  # Genre field
    duration = models.CharField(max_length=50)
    category = models.CharField(max_length=100)  # Movie, Concert, Play
    description = models.TextField(blank=True, null=True)  # Description field
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.message}"
