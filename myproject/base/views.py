from django.shortcuts import render, redirect, get_object_or_404
from .models import Article, Category
from .forms import ArticleForm, CategoryForm
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse

# REST Framework imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Import your serializers (make sure these files exist)
from .serializers import UserSerializer, RegisterSerializer

# ==================== API VIEWS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """User Registration API"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful!'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """User Login API"""
    from .serializers import LoginSerializer
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login successful!'
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== WEB VIEWS ====================

# Signup View
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Check if passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('signup')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # Log the user in
        login(request, user)  # Fixed: Use django.contrib.auth.login
        messages.success(request, f'Welcome {username}! Your account has been created successfully.')
        return redirect('read_article')
    
    return render(request, 'signup.html')

# Signin View
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)  # Fixed: Use django.contrib.auth.login
            messages.success(request, f'Welcome back, {username}!')
            return redirect('read_article')
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('signin')
    
    return render(request, 'signin.html')

# Signout View
def signout(request):
    if request.method == 'POST':
        logout(request)  # Fixed: Use django.contrib.auth.logout
        messages.success(request, 'You have been logged out successfully!')
        return redirect('signin')
    return render(request, 'signout.html')

# Profile View
@login_required(login_url='signin')
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

# Update Profile View
@login_required(login_url='signin')
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Check if username is taken by another user
        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return redirect('profile')
        
        # Check if email is taken by another user
        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('profile')
        
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return redirect('profile')

# Change Password View
@login_required(login_url='signin')
def change_password(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Check if old password is correct
        if not user.check_password(old_password):
            messages.error(request, 'Current password is incorrect!')
            return redirect('profile')
        
        # Check if new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match!')
            return redirect('profile')
        
        # Check password length
        if len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return redirect('profile')
        
        # Change password
        user.set_password(new_password1)
        user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')
    
    return redirect('profile')

# ==================== CATEGORY VIEWS ====================

@login_required(login_url='signin')
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('read_category')
        else:
            print(form.errors)
    else:
        form = CategoryForm()
    return render(request, 'create_category.html', {'form': form})

def read_category(request):
    search = request.GET.get('q')
    if search:
        data = Category.objects.filter(
            Q(name__icontains=search) |
            Q(desc__icontains=search)
        )
    else:
        data = Category.objects.all()
    return render(request, 'read_category.html', {'data': data, 'search': search})

def update_category(request, pk):
    data = get_object_or_404(Category, id=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=data)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{data.name}" updated successfully!')
            return redirect('read_category')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=data)
    
    return render(request, 'update_category.html', {'form': form})

def delete_category(request, pk):
    data = get_object_or_404(Category, id=pk)
    if request.method == 'POST':
        category_name = data.name
        data.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('read_category')
    return render(request, 'delete_category.html', {'data': data})

# ==================== ARTICLE VIEWS ====================

@login_required(login_url='signin')
def home(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article created successfully!.....')
            return redirect('read_article')
    else:
        form = ArticleForm()
    return render(request, 'home.html', {'form': form})

@login_required(login_url='signin')
def read_article(request):
    search = request.GET.get('q')
    category_id = request.GET.get('category')
    data = Article.objects.filter(is_deleted=False)
    if search:
        data = data.filter(
            Q(title__icontains=search) |
            Q(desc__icontains=search) |
            Q(author__icontains=search) |
            Q(cost__icontains=search) |
            Q(type__name__icontains=search)
        )
    if category_id:
        data = data.filter(type__id=category_id)
        
    categories = Category.objects.all()    
    return render(request, 'read_article.html', {
        'data': data,
        'search': search,
        'categories': categories,
        'selected_category': category_id
    })

@login_required(login_url='signin')
def update_article(request, pk):
    data = get_object_or_404(Article, id=pk, is_deleted=False)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=data)  # Make sure request.FILES is included
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully!.....')
            return redirect('read_article')
    else:
        form = ArticleForm(instance=data)
    return render(request, 'update_article.html', {'form': form})

@login_required(login_url='signin')
def delete_article(request, pk):
    data = get_object_or_404(Article, id=pk, is_deleted=False)
    if request.method == 'POST':
        data.is_deleted = True
        data.deleted_at = timezone.now()
        data.save()
        messages.success(request, f'Article "{data.title}" has been moved to trash!')
        return redirect('read_article')
    return render(request, 'delete_article.html', {'data': data})

@login_required(login_url='signin')
def history_article(request):
    search = request.GET.get('q')
    category_id = request.GET.get('category')
    data = Article.objects.filter(is_deleted=True)
    if search:
        data = data.filter(
            Q(title__icontains=search) |
            Q(desc__icontains=search) |
            Q(author__icontains=search) |
            Q(cost__icontains=search)
        )
    if category_id:
        data = data.filter(type__id=category_id)
    categories = Category.objects.all()
    return render(request, 'history_article.html', {
        'data': data,
        'search': search,
        'categories': categories,
        'selected_category': category_id
    })

@login_required(login_url='signin')
def restore_article(request, pk):
    data = get_object_or_404(Article, id=pk, is_deleted=True)
    if request.method == 'POST':
        data.is_deleted = False
        data.deleted_at = None
        data.save()
        messages.success(request, 'Article Restored successfully!.....')
        return redirect('history_article')
    return render(request, 'restore_article.html', {'data': data})