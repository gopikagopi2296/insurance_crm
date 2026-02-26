from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,auth
from django.contrib import messages
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
import re
import random
from .models import Agent,Campaign,Client,Contact
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse


# Create your views here.
def home(request):
    return render(request,'home.html')

def loginpage(request):
    return render(request,'loginpage.html')

def login1(request):
    if request.method == "POST":
        username=request.POST['username']
        password=request.POST['password']
        user=auth.authenticate(username=username,password=password)
        if user is not None:
            if user.is_staff==1:
                login(request,user)
                return redirect('adminhome')
            else:    
                auth.login(request,user)
                return redirect('agenthome')
        else:
            messages.info(request,"Invalid username or password")
            return redirect('loginpage')
    return render(request,'login.html')


@login_required(login_url='loginpage')
def adminhome(request):
    return render(request,'adminhome.html') 

@login_required(login_url='loginpage')
def add_agent(request):
    return render(request,'add_agent.html')

@login_required(login_url='loginpage')
def add_agentdb(request):
    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        contact = request.POST.get('mobile')
        dob = request.POST.get('dob')
        specialization = request.POST.get('specialization')
        image = request.FILES.get('image')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('add_agent')
        if not contact:
            messages.error(request, "Mobile number is required")
            return redirect('add_agent')

        if not re.fullmatch(r'^[6-9]\d{9}$', contact):
            messages.error(request, "Enter a valid 10-digit mobile number")
            return redirect('add_agent')
 
        if (
            Agent.objects.filter(phone_number=contact).exists() or
            Client.objects.filter(mobile=contact).exists()
        ):
            messages.error(request, "Mobile number already exists")
            return redirect('add_agent')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('add_agent')
        
        if not email.endswith('@gmail.com'):
            messages.error(request,'Invalid email')
            return redirect('add_agent') 




        password = str(random.randint(100000, 999999))

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=fname,
            last_name=lname,
            password=password,

        )
        user.save()


        agent=Agent.objects.create(
            user=user,
            phone_number=contact,
            dob=dob,
            specialization=specialization,
            img=image
        )

        agent.save()
        
        send_mail(
            subject="Welcome to SecureLife – Agent Account Created",
            message=(
                f"Hello {fname},\n\n"
                "Your Agent account has been successfully created on SecureLife.\n\n"
                "Login Credentials:\n"
                f"Username: {username}\n"
                f"Temporary Password: {password}\n\n"
                "For security reasons, please log in and change your password immediately.\n\n"
                "Regards,\n"
                "SecureLife Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )


        messages.success(request, "Agent added successfully")
        return redirect('add_agent')
    
@login_required(login_url='loginpage')
def view_agent(request):
    agent=Agent.objects.all().order_by('-id')
    return render(request,'view_agent.html',{'agents':agent})

@login_required(login_url='loginpage')
def edit_agent(request,pk):
    agent=Agent.objects.get(id=pk)
    return render(request,'edit_agent.html',{'a':agent})


@login_required(login_url='loginpage')
def edit_agentdb(request, pk):
    agent = get_object_or_404(Agent, id=pk)
    user = agent.user

    old_username = user.username  # 

    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        contact = request.POST.get('mobile')
        dob = request.POST.get('dob')
        specialization = request.POST.get('specialization')

        # ---------- VALIDATIONS ----------

        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('edit_agent', pk=pk)

        if (
            Agent.objects.exclude(id=agent.id).filter(phone_number=contact).exists()
            or Client.objects.filter(mobile=contact).exists()
        ):
            messages.error(request, "Mobile number already exists")
            return redirect('edit_agent', pk=pk)

        if not re.fullmatch(r'^[6-9]\d{9}$', contact):
            messages.error(request, "Invalid mobile number")
            return redirect('edit_agent', pk=pk)

        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('edit_agent', pk=pk)

        if not email.endswith('@gmail.com'):
            messages.error(request, "Invalid email address")
            return redirect('edit_agent', pk=pk)



        # ---------- UPDATE USER ----------
        user.first_name = fname
        user.last_name = lname
        user.username = username
        user.email = email
        user.save()

        # ---------- UPDATE AGENT ----------
        agent.phone_number = contact
        agent.dob = dob
        agent.specialization = specialization

        if request.FILES.get('image'):
            agent.img = request.FILES.get('image')

        agent.save()

        # ---------- EMAIL (ONLY IF USERNAME CHANGED) ----------
        if old_username != username:
            send_mail(
                subject="Profile Updated – SecureLife",
                message=(
                    f"Hello {user.first_name},\n\n"
                    "Your profile has been updated by the administrator.\n\n"
                    f"New Username: {user.username}\n\n"
                    "Regards,\n"
                    "SecureLife Team"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )

        messages.success(request, "Agent updated successfully")
        return redirect('view_agent')

    return render(request, 'edit_agent.html', {'agent': agent})



@login_required(login_url='loginpage')
def a_delete(request, pk):
    agent = get_object_or_404(Agent, id=pk)
    user = agent.user

    if request.user == user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('view_agent')

    agent.delete()
    user.delete()

    messages.success(request, "Agent deleted successfully.")
    return redirect('view_agent')

@login_required(login_url='loginpage')
def add_campaign(request):
    agent=Agent.objects.all()
    return render(request,'add_campaign.html',{'agents':agent})    



@login_required(login_url='loginpage')
def add_campaigndb(request):
    if request.method == 'POST':
        campaign_name = request.POST.get('campaign_name')
        date = request.POST.get('date')
        time = request.POST.get('time')
        place = request.POST.get('place')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        agent_id = request.POST.get('agent_id')

        # Basic validation
        if not all([campaign_name, date, time, place, latitude, longitude, agent_id]):
            messages.error(request, "All fields are required.")
            return redirect('add_campaign')

        # Create campaign
        Campaign.objects.create(
            campaign_name=campaign_name,
            date=date,
            time=time,
            place=place,
            latitude=latitude,
            longitude=longitude,
            agent_id=agent_id
        )

        messages.success(request, "Campaign added successfully!")
        return redirect('add_campaign')

    agents = Agent.objects.all()
    return render(request, 'add_campaign.html', {'agents': agents})


@login_required(login_url='loginpage')
def view_campaigns(request):
    campaigns = Campaign.objects.select_related('agent').order_by('-date')
    return render(request, 'view_campaigns.html', {'campaigns': campaigns})


@login_required(login_url='loginpage')
def edit_campaign(request, pk):
    campaign = get_object_or_404(Campaign, id=pk)
    agents = Agent.objects.all()

    if request.method == 'POST':
        campaign.campaign_name = request.POST.get('campaign_name')
        campaign.date = request.POST.get('date')
        campaign.time = request.POST.get('time')
        campaign.place = request.POST.get('place')
        campaign.latitude = request.POST.get('latitude')
        campaign.longitude = request.POST.get('longitude')
        campaign.agent_id = request.POST.get('agent_id')

        campaign.save()
        messages.success(request, "Campaign updated successfully!")
        return redirect('view_campaigns')

    return render(
        request,
        'edit_campaign.html',
        {
            'campaign': campaign,
            'agents': agents
        }
    )


@login_required(login_url='loginpage')
def delete_campaign(request, pk):
    campaign = get_object_or_404(Campaign, id=pk)
    campaign.delete()
    messages.success(request, "Campaign deleted successfully!")
    return redirect('view_campaigns')


def logout(request):
    auth.logout(request)
    return redirect('home') 

@login_required(login_url='loginpage')
def agenthome(request):
    agent = Agent.objects.get(user=request.user)
    campaigns = Campaign.objects.filter(agent=agent)

    context = {
        'campaigns': campaigns,
        'campaign_count': campaigns.count(),
    }

    return render(request, 'agenthome.html', context)

@login_required(login_url='loginpage')
def assigned_campaigns(request):
    agent = Agent.objects.get(user=request.user)
    campaigns = Campaign.objects.filter(agent=agent)
    return render(request, 'assigned_campaigns.html', {'campaigns': campaigns})


@login_required(login_url='loginpage')
def add_client(request):
    agent = Agent.objects.get(user=request.user)
    campaigns = Campaign.objects.filter(agent=agent)
    return render(request, 'add_client.html', {'campaigns': campaigns})

@login_required(login_url='loginpage')
def add_clientdb(request):
    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('mobile')

        qualification = request.POST.get('qualification')
        salary = request.POST.get('salary')
        marital = request.POST.get('marital')
        children = request.POST.get('children')

        previous_policy = request.POST.get('previous_policy')
        willing = request.POST.get('willing')
        policy_number = request.POST.get('policy_number')

        rating = request.POST.get('rating')
        experience = request.POST.get('experience')
        feedback = request.POST.get('feedback')

        aadhar = request.POST.get('aadhar')
        pan = request.POST.get('pan')
        address = request.POST.get('address')
        campaign_id = request.POST.get('campaign_id')
        image = request.FILES.get('image')

        # ---------- VALIDATIONS ----------
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('add_client')
        if not email.endswith('@gmail.com'):
            messages.error(request,'Invalid email')
            return redirect('add_client') 

        if not re.match(r'^[6-9]\d{9}$', contact):
            messages.error(request, "Invalid mobile number")
            return redirect('add_client')

        if (
            Client.objects.filter(mobile=contact).exists() or
            Agent.objects.filter(phone_number=contact).exists()
        ):
            messages.error(request, "Mobile number already exists")
            return redirect('add_client')


        if not re.match(r'^[0-9]{12}$', aadhar):
            messages.error(request, "Invalid Aadhaar number")
            return redirect('add_client')

        if Client.objects.filter(aadhar=aadhar).exists():
            messages.error(request, "Aadhaar already exists")
            return redirect('add_client')

        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
            messages.error(request, "Invalid PAN number")
            return redirect('add_client')

        if Client.objects.filter(pan=pan).exists():
            messages.error(request, "PAN already exists")
            return redirect('add_client')

        # ---------- CREATE USER ----------

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=fname,
            last_name=lname,
        )

        # ---------- CREATE CLIENT ----------
        agent = Agent.objects.get(user=request.user)
        campaign = Campaign.objects.get(id=campaign_id)

        Client.objects.create(
            user=user,
            mobile=contact,
            qualification=qualification,
            salary=salary,
            marital_status=marital,
            children=children,
            previous_policy=previous_policy,
            willing_to_switch=willing,
            policy_number=policy_number,
            rating=rating,
            experience=experience,
            feedback=feedback,
            aadhar=aadhar,
            pan=pan,
            address=address,
            image=image,
            agent=agent,
            campaign=campaign
        )

        messages.success(request, "Client added successfully")
        return redirect('add_client')
    

@login_required(login_url='loginpage')
def view_clients(request):
    agent = Agent.objects.get(user=request.user)
    clients = Client.objects.filter(agent=agent)
    return render(request, 'view_clients.html', {'clients': clients})



@login_required(login_url='loginpage')
def client_detail(request, pk):
    client = Client.objects.get(id=pk, agent__user=request.user)
    return render(request, 'client_detail.html', {'client': client})


@login_required(login_url='loginpage')
def delete_client(request, pk):
    client = Client.objects.get(id=pk, agent__user=request.user)
    client.user.delete()  
    messages.success(request, "Client deleted successfully")
    return redirect('view_clients')

@login_required(login_url='loginpage')
def edit_client(request, pk):
    agent = Agent.objects.get(user=request.user)
    client = Client.objects.get(id=pk, agent__user=request.user)
    campaigns = Campaign.objects.filter(agent=agent)
    return render(request, 'edit_client.html', {'campaigns': campaigns,'client': client,})


@login_required(login_url='loginpage')
def edit_clientdb(request, pk):
    client = Client.objects.get(id=pk, agent__user=request.user)
    user = client.user

    if request.method == "POST":

        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('mobile')

        qualification = request.POST.get('qualification')
        salary = request.POST.get('salary')
        marital = request.POST.get('marital')
        children = request.POST.get('children')

        previous_policy = request.POST.get('previous_policy')
        willing = request.POST.get('willing')
        policy_number = request.POST.get('policy_number')

        rating = request.POST.get('rating')
        experience = request.POST.get('experience')
        feedback = request.POST.get('feedback')

        aadhar = request.POST.get('aadhar')
        pan = request.POST.get('pan')
        address = request.POST.get('address')
        campaign_id = request.POST.get('campaign_id')
        image = request.FILES.get('image')

        # ---------- VALIDATIONS ----------
        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('edit_client', pk=pk)
        if not email.endswith('@gmail.com'):
            messages.error(request,'Invalid email')
            return redirect('edit_client', pk=pk) 

        if not re.match(r'^[6-9]\d{9}$', contact):
            messages.error(request, "Invalid mobile number")
            return redirect('edit_client', pk=pk)

        if (
            Client.objects.exclude(id=client.id).filter(mobile=contact).exists() or
            Agent.objects.filter(phone_number=contact).exists()
        ):
            messages.error(request, "Mobile number already exists")
            return redirect('edit_client', pk=pk)


        if not re.match(r'^[0-9]{12}$', aadhar):
            messages.error(request, "Invalid Aadhaar number")
            return redirect('edit_client', pk=pk)

        if Client.objects.exclude(id=client.id).filter(aadhar=aadhar).exists():
            messages.error(request, "Aadhaar already exists")
            return redirect('edit_client', pk=pk)

        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
            messages.error(request, "Invalid PAN number")
            return redirect('edit_client', pk=pk)

        if Client.objects.exclude(id=client.id).filter(pan=pan).exists():
            messages.error(request, "PAN already exists")
            return redirect('edit_client', pk=pk)

        # ---------- UPDATE USER ----------
        user.first_name = fname
        user.last_name = lname
        user.email = email
        user.username = email
        user.save()

        # ---------- UPDATE CLIENT ----------
        client.mobile = contact
        client.qualification = qualification
        client.salary = salary
        client.marital_status = marital
        client.children = children
        client.previous_policy = previous_policy
        client.willing_to_switch = willing
        client.policy_number = policy_number
        client.rating = rating
        client.experience = experience
        client.feedback = feedback
        client.aadhar = aadhar
        client.pan = pan
        client.address = address
        client.campaign_id = campaign_id

        if image:
            client.image = image

        client.save()

        messages.success(request, "Client updated successfully")
        return redirect('view_clients')
    

@login_required(login_url='loginpage')
def edit_profile(request):
    agent = Agent.objects.get(user=request.user)
    return render(request, 'edit_profile.html', {'user': request.user,'agent': agent})


@login_required(login_url='loginpage')
def edit_profiledb(request):
    user = request.user
    agent = Agent.objects.get(user=user)

    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        dob = request.POST.get('dob')
        specialization = request.POST.get('specialization')
        image = request.FILES.get('image')

        # VALIDATIONS
        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('edit_profile')
        
        if not re.match(r'^[6-9]\d{9}$', mobile):
            messages.error(request, "Invalid mobile number")
            return redirect('edit_profile')

        if (Agent.objects.exclude(id=agent.id).filter(phone_number=mobile).exists() or Client.objects.filter(mobile=mobile).exists()):
            messages.error(request, "Mobile number already exists")
            return redirect('edit_profile')

        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('edit_profile')




        # UPDATE USER
        user.first_name = fname
        user.last_name = lname
        user.username = username
        user.email = email
        user.save()

        # UPDATE AGENT
        agent.phone_number = mobile
        agent.dob = dob
        agent.specialization = specialization
        if image:
            agent.img = image
        agent.save()

        messages.success(request, "Profile updated successfully")
        return redirect('view_profile')
    

@login_required(login_url='loginpage')
def view_profile(request):
    agent = Agent.objects.get(user=request.user)
    return render(request, 'view_profile.html', {'user': request.user,'agent': agent})


@login_required(login_url='loginpage')
def r_password(request):
    return render(request, 'reset_password.html')


@login_required(login_url='loginpage')
def reset(request):
    if request.method=='POST':
        c_pwd=request.POST['cpassword']
        n_pwd=request.POST['npassword']
        c_npwd=request.POST['cnpassword']
        usr = request.user.id #Get the logged-in user
        tsr=User.objects.get(id=usr) #fetch user from the database

        #check if the entered current password matches the stored password
        if not check_password(c_pwd,tsr.password):
            messages.error(request,'current password is incorrect!')
            return redirect('r_password')
        if n_pwd==c_npwd:
            if len(n_pwd) < 6 or not any(char.isupper() for char in n_pwd) \
                or not any(char.isdigit() for char in n_pwd)\
                or not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?/~' for char in n_pwd):
                messages.error(request,'Password must be at least 6 character long and contain at least one uppercase letter,one digit,and one special character. ')
                return redirect('r_password')
            
            else:
                tsr.password=n_pwd
                tsr.set_password(n_pwd)
                tsr.save()
                messages.success(request,"password changed successfully")
                return redirect('loginpage')
        messages.error(request,'new password and confirm new password doesnot match!')
        return redirect('r_password')
    
@login_required(login_url='loginpage')
def admin_view_clients(request):
    clients = Client.objects.select_related('user').all().order_by('-id')
    return render(request, 'admin_view_clients.html', {'clients': clients})

@login_required(login_url='loginpage')
def admin_client_detail(request, pk):
    client = get_object_or_404(Client, id=pk)
    return render(request, 'admin_client_detail.html', {'client': client})


def contactdb(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Save to DB
        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Email content
        user_subject = "We received your message – SecureLife Insurance"
        user_message = f"""
Dear {name},

Thank you for contacting SecureLife Insurance.

We have received your message regarding:
"{subject}"

Our team will get back to you shortly.

Best regards,
SecureLife Insurance Team
"""

        # Send email
        send_mail(
            user_subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return redirect('home')


def ajax_validate_user_fields(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()
    user_id = request.GET.get('user_id')          # edit profile
    agent_user_id = request.GET.get('agent_user') # edit agent (agent.user.id)
    agent_id = request.GET.get('agent_id')
    client_user_id = request.GET.get('client_user')
    client_id = request.GET.get('client_id')

    # normalize empty strings
    user_id = user_id or None
    agent_user_id = agent_user_id or None
    agent_id = agent_id or None
    client_user_id = client_user_id or None
    client_id = client_id or None

    response = {
        'valid': True,
        'message': ''
    }

    # USERNAME CHECK
    if field == 'username':
        qs = User.objects.filter(username__iexact=value)

        if user_id:
            qs = qs.exclude(id=user_id)
        if agent_user_id:
            qs = qs.exclude(id=agent_user_id)
        if client_user_id:
            qs = qs.exclude(id=client_user_id)

        if qs.exists():
            response['valid'] = False
            response['message'] = "Username already exists"

    # MOBILE CHECK
    elif field == 'mobile':
        pattern = r'^[6-9]\d{9}$'
        if not re.match(pattern, value):
            response['valid'] = False
            response['message'] = "Enter a valid 10-digit mobile number"
        else:
            agent_qs = Agent.objects.filter(phone_number=value)
            client_qs = Client.objects.filter(mobile=value)

            # exclude current agent
            if agent_id:
                agent_qs = agent_qs.exclude(id=agent_id)

            # exclude current client
            if client_id:
                client_qs = client_qs.exclude(id=client_id)

            if agent_qs.exists() or client_qs.exists():
                response['valid'] = False
                response['message'] = "Mobile number already exists"

    # EMAIL CHECK
    elif field == 'email':
        if not re.fullmatch(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', value):
            response['valid'] = False
            response['message'] = "Invalid email"
        else:
            qs = User.objects.filter(email__iexact=value)

            if user_id:
                qs = qs.exclude(id=user_id)
            if agent_user_id:
                qs = qs.exclude(id=agent_user_id)
            if client_user_id:
                qs = qs.exclude(id=client_user_id)

            if qs.exists():
                response['valid'] = False
                response['message'] = "Email already exists"


   #AADHAR
    elif field == 'aadhar':
        if not re.fullmatch(r'^[0-9]{12}$', value):
            response['valid'] = False
            response['message'] = "Aadhaar must be 12 digits"
        elif Client.objects.filter(aadhar=value).exists():
            response['valid'] = False
            response['message'] = "Aadhaar already exists"

    #PAN
    elif field == 'pan':
        if not re.fullmatch(r'^[A-Z]{5}[0-9]{4}[A-Z]$', value):
            response['valid'] = False
            response['message'] = "Invalid PAN format (ABCDE1234F)"
        elif Client.objects.filter(pan=value).exists():
            response['valid'] = False
            response['message'] = "PAN already exists"


    return JsonResponse(response) 


@login_required
def ajax_validate_reset_password(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '')
    confirm = request.GET.get('confirm', '')

    response = {'valid': True, 'message': ''}

    user = request.user

    # CURRENT PASSWORD CHECK
    if field == 'cpassword':
        if not check_password(value, user.password):
            response['valid'] = False
            response['message'] = "Current password is incorrect"

    # NEW PASSWORD CHECK
    elif field == 'npassword':
        
        if (
            len(value) < 6 or
            not any(c.isupper() for c in value) or
            not any(c.isdigit() for c in value) or
            not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~]', value)
        ):
            response['valid'] = False
            response['message'] = (
                "Password must be at least 6 characters long and contain "
                "at least one uppercase letter, one digit, and one special character."
            )

    # CONFIRM PASSWORD CHECK
    elif field == 'cnpassword':
        if value != confirm:
            response['valid'] = False
            response['message'] = "Passwords do not match"

    return JsonResponse(response)



def ajax_login_validate(request):
    field = request.GET.get('field')
    username = request.GET.get('username', '').strip()
    password = request.GET.get('password', '').strip()

    response = {'valid': True, 'message': ''}

    # USERNAME CHECK
    if field == 'username':
        if not User.objects.filter(username=username).exists():
            response['valid'] = False
            response['message'] = "Username does not exist"

    # PASSWORD CHECK
    elif field == 'password':
        if not username:
            response['valid'] = False
            response['message'] = "Enter username first"
        else:
            user = authenticate(username=username, password=password)
            if user is None:
                response['valid'] = False
                response['message'] = "Invalid password"

    return JsonResponse(response)
