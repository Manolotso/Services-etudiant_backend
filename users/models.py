from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

################################################

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=10,
        choices=[
            ('admin', 'Admin'),
            ('student', 'Student')
        ],
        default='student'
    )

    must_change_password = models.BooleanField(default=True)

    custom_username = models.CharField(max_length=150, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()   # 🔥 IMPORTANT

    def __str__(self):
        return self.email
    
#############################################

class RegistrationRequest(models.Model):
    email = models.EmailField(unique=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

#################################

class Course(models.Model):
    name = models.CharField(max_length=255)
    teacher = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
################################ 


class Room(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
################################


class Schedule(models.Model):
    DAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)

    day = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course} - {self.day}"

############################################################################################

class Job(models.Model):
    TYPE_CHOICES = [
        ('internship', 'Internship'),
        ('job', 'Job'),
        ('freelance', 'Freelance'),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    company_link = models.URLField(blank=True, null=True) # Ajouté
    
    description = models.TextField(blank=True, null=True)
    link = models.URLField(unique=True) # unique=True évite les doublons
    
    location = models.CharField(max_length=255, blank=True, null=True) # Ajouté
    contract = models.CharField(max_length=50, blank=True, null=True) # Ajouté
    category = models.CharField(max_length=100, blank=True, null=True) # Ajouté

    job_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.company}"
    
    
