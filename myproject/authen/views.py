from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout,update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Create your views here.
#register
def signup(request):
    if request.method=="POST":
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        email=request.POST['email']
        username=request.POST['username']
        password=request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request,'user already exist')
        elif User.objects.filter(email=email).exists():
            messages.error(request,'email already exist')
        else:
            User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
        )#registreation success
        messages.success(request,'user registered successfully.......')
        return redirect('signin')
    return render(request,'signup.html')


#login
def signin(request):
    if request.method=="POST":
        User=authenticate(request,
            username=request.POST['username'],
            password=request.POST['password'],
        )
        if User:
            login(request,User)
            messages.success(request,'user login successfully.......')
            return redirect('profile')
        else:
             messages.error(request,'invalid credentials..')
        return redirect('signin')
    return render(request,'signin.html')

#profile
@login_required(login_url='signin')
def profile(request):
    #extract the active user
    data=request.user
    return render(request,'profile.html', {'data':data})

@login_required(login_url='signin')
def update_profile(request): 
    #extract the details of current active useer and his p details
    data=request.user
    if request.method=="POST":
        data.first_name=request.POST['first_name']
        data.last_name=request.POST['last_name']
        data.email=request.POST['email']
        data.username=request.POST['username']
        data.save()
        messages.success(request,'profile updated successfully')
        return redirect('profile')
    return render(request,'update_profile.html',{'data':data})

@login_required(login_url='signin')
def update_password(request):
    #extract the currently active user and update his password
    data=request.user
    if request.method=="POST":
        old_password=request.POST['old_password']
        new_password=request.POST['new_password']
        confirm_password=request.POST['confirm_password']

        #check password-->verify the old password
        if not data.check_password(old_password):
            messages.error(request,'old password is not valid')
        
        elif new_password==old_password:
            messages.error(request,'new password is similar to old password')

        elif new_password != confirm_password:
            messages.error(request,'new password do not match')

        else:
            data.set_password(new_password) #to encrypt the new password
            data.save()
            update_session_auth_hash(request,data)
            messages.success(request,'password updated successfully')
            return redirect('profile')
    return render(request,'update_password.html')

@login_required(login_url='signin')
def signout(request):
    if request.method=='POST':
        logout(request)
        messages.success(request,'user logged out successfully..')
        return redirect(signin)
    return render(request,'signout.html')
