from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (CustomerViewSet, MeasurementViewSet, FabricViewSet, 
                   OrderViewSet, PaymentViewSet, OrderFinancialsViewSet,
                   SubscriptionViewSet, ActivityLogViewSet, RoleViewSet, UserProfileViewSet,
                   register, login, logout, dashboard_stats, UserViewSet, delete_user)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'measurements', MeasurementViewSet, basename='measurement')
router.register(r'fabrics', FabricViewSet, basename='fabric')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'financials', OrderFinancialsViewSet, basename='financials')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'activities', ActivityLogViewSet, basename='activity')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    path('auth/logout/', logout, name='logout'),
    path('auth/users/<int:user_id>/delete/', delete_user, name='delete-user'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    # path('users/', users, name='users'),
    path('', include(router.urls)),
]