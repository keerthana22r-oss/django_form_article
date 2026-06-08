# base/api_views.py
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Category, Article
from .serializers import (
    CategorySerializer, 
    ArticleSerializer, 
    ArticleCreateUpdateSerializer,
    UserSerializer, 
    LoginSerializer, 
    RegisterSerializer
)




# Custom Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# ============ AUTHENTICATION APIS ============

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """User Logout API"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_api(request):
    """Get User Profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_api(request):
    """Update User Profile"""
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'user': serializer.data, 'message': 'Profile updated!'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ============ CATEGORY APIS ============

class CategoryListCreateAPI(generics.ListCreateAPIView):
    """List all categories or create a new category"""
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'desc']
    ordering_fields = ['name', 'created_at']
    pagination_class = StandardResultsSetPagination

class CategoryRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

# ============ ARTICLE APIS ============

class ArticleListCreateAPI(generics.ListCreateAPIView):
    """List all active articles or create a new article"""
    queryset = Article.objects.filter(is_deleted=False).order_by('-id')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'desc', 'author', 'type__name']
    ordering_fields = ['cost', 'title', 'id', 'created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ArticleCreateUpdateSerializer
        return ArticleSerializer
    
    def perform_create(self, serializer):
        serializer.save()

class ArticleRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete (soft delete) an article"""
    queryset = Article.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ArticleCreateUpdateSerializer
        return ArticleSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete article"""
        article = self.get_object()
        article.is_deleted = True
        article.save()
        return Response({'message': 'Article moved to trash'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deleted_articles_api(request):
    """Get all deleted articles (history)"""
    deleted_articles = Article.objects.filter(is_deleted=True)
    search = request.GET.get('search')
    category_id = request.GET.get('category')
    
    if search:
        deleted_articles = deleted_articles.filter(
            Q(title__icontains=search) |
            Q(desc__icontains=search) |
            Q(author__icontains=search)
        )
    if category_id:
        deleted_articles = deleted_articles.filter(type_id=category_id)
    
    serializer = ArticleSerializer(deleted_articles, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_article_api(request, pk):
    """Restore a deleted article"""
    try:
        article = Article.objects.get(id=pk, is_deleted=True)
        article.is_deleted = False
        article.save()
        return Response({'message': 'Article restored successfully!'})
    except Article.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

# ============ STATISTICS APIS ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_api(request):
    """Get dashboard statistics"""
    stats = {
        'total_articles': Article.objects.filter(is_deleted=False).count(),
        'total_categories': Category.objects.count(),
        'deleted_articles': Article.objects.filter(is_deleted=True).count(),
        'recent_articles': ArticleSerializer(
            Article.objects.filter(is_deleted=False).order_by('-id')[:5], 
            many=True
        ).data
    }
    return Response(stats)

@api_view(['GET'])
@permission_classes([AllowAny])  # No authentication required
def test_api(request):
    return Response({
        'message': 'API is working!',
        'status': 'success',
        'timestamp': str(timezone.now())
    })