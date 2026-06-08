from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views, api_views

# API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="ArticleHub API",
        default_version='v1',
        description="API documentation for ArticleHub Project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@articlehub.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Web URLs (existing)
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Category URLs
    path('create_category/', views.create_category, name='create_category'),
    path('read_category/', views.read_category, name='read_category'),
    path('update_category/<int:pk>/', views.update_category, name='update_category'),
    path('delete_category/<int:pk>/', views.delete_category, name='delete_category'),
    
    # Article URLs
    path('', views.home, name='home'),
    path('read_article/', views.read_article, name='read_article'),
    path('update_article/<int:pk>/', views.update_article, name='update_article'),
    path('delete_article/<int:pk>/', views.delete_article, name='delete_article'),
    path('history_article/', views.history_article, name='history_article'),
    path('restore_article/<int:pk>/', views.restore_article, name='restore_article'),
    
    # ============ API URLs ============
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/docs.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Authentication APIs
    path('api/register/', api_views.register_api, name='api_register'),
    path('api/login/', api_views.login_api, name='api_login'),
    path('api/logout/', api_views.logout_api, name='api_logout'),
    path('api/profile/', api_views.profile_api, name='api_profile'),
    path('api/profile/update/', api_views.update_profile_api, name='api_update_profile'),
    
    # JWT Token APIs
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Category APIs
    path('api/categories/', api_views.CategoryListCreateAPI.as_view(), name='api_categories'),
    path('api/categories/<int:pk>/', api_views.CategoryRetrieveUpdateDeleteAPI.as_view(), name='api_category_detail'),
    
    # Article APIs
    path('api/articles/', api_views.ArticleListCreateAPI.as_view(), name='api_articles'),
    path('api/articles/<int:pk>/', api_views.ArticleRetrieveUpdateDeleteAPI.as_view(), name='api_article_detail'),
    path('api/articles/deleted/', api_views.deleted_articles_api, name='api_deleted_articles'),
    path('api/articles/<int:pk>/restore/', api_views.restore_article_api, name='api_restore_article'),
    
    # Statistics API
    path('api/stats/', api_views.dashboard_stats_api, name='api_stats'),

    path('api/test/', api_views.test_api, name='api_test'),
]