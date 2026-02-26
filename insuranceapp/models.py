from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Agent(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    dob=models.DateField()
    specialization=models.CharField(max_length=255)
    img= models.ImageField(blank=True,upload_to="image/",null=True)

class Campaign(models.Model):
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    campaign_name = models.CharField(max_length=200)

    date = models.DateField()
    time = models.TimeField()

    place = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)



class Client(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    agent = models.ForeignKey(Agent,on_delete=models.CASCADE,null=True)
    campaign = models.ForeignKey(Campaign,on_delete=models.CASCADE,null=True)
    mobile = models.CharField(max_length=10)
    qualification = models.CharField(max_length=150)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    MARITAL_CHOICES = (
        ('single', 'Single'),
        ('married', 'Married'),
    )
    marital_status = models.CharField(max_length=10, choices=MARITAL_CHOICES)

    children = models.PositiveIntegerField(null=True, blank=True)

    PREVIOUS_POLICY_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
    )
    previous_policy = models.CharField(max_length=3, choices=PREVIOUS_POLICY_CHOICES)

    willing_to_switch = models.CharField(max_length=3,choices=PREVIOUS_POLICY_CHOICES,null=True,blank=True)

    policy_number = models.CharField(max_length=50, null=True, blank=True)

    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    aadhar = models.CharField(max_length=12, unique=True)
    pan = models.CharField(max_length=10, unique=True)


    address = models.TextField()
    image = models.ImageField(upload_to='clients/', null=True, blank=True)


class Contact(models.Model):
    name = models.CharField(max_length=100,null=True)
    email = models.EmailField(null=True)
    subject = models.CharField(max_length=150 , null=True)
    message = models.TextField(null=True)




