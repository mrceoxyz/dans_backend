from rest_framework import permissions

class HasPermission(permissions.BasePermission):
    """Custom permission class to check user profile permissions"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser has all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Map view actions to permissions
        permission_map = {
            'CustomerViewSet': 'can_manage_customers',
            'OrderViewSet': 'can_manage_orders',
            'PaymentViewSet': 'can_manage_payments',
            'FabricViewSet': 'can_manage_fabrics',
            'MeasurementViewSet': 'can_manage_measurements',
        }
        
        view_name = view.__class__.__name__
        required_permission = permission_map.get(view_name)
        
        if not required_permission:
            return True  # No specific permission required
        
        # For read-only actions, allow if user can view
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write actions, check specific permission
        return getattr(profile, required_permission, False)


class CanManageUsers(permissions.BasePermission):
    """Permission to manage users"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.can_manage_users
        
        return False