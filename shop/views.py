from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from .models import Customer, Measurement, Fabric, Order, Payment, OrderFinancials, Subscription, ActivityLog, Role, UserProfile
from .serializers import (CustomerSerializer, MeasurementSerializer, RegisterSerializer, 
                         UserSerializer, FabricSerializer, OrderSerializer, OrderListSerializer,
                         PaymentSerializer, OrderFinancialsSerializer, SubscriptionSerializer,
                         ActivityLogSerializer, RoleSerializer, UserProfileSerializer)
from .permissions import HasPermission, CanManageUsers

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_activity(user, action, resource_type, resource_id=None, resource_name='', description='', request=None):
    """Helper function to log user activities"""
    ip_address = get_client_ip(request) if request else None
    ActivityLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        description=description,
        ip_address=ip_address
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        # Log registration activity
        log_activity(user, 'create', 'user', user.id, user.username, 'User registered', request)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'subscription': SubscriptionSerializer(user.subscription).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        
        # Get or create subscription if it doesn't exist
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={'plan': 'free', 'status': 'active'}
        )
        if created:
            subscription.set_plan_limits()
            subscription.save()
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created and not profile.role:
            # Assign default owner role if no role exists
            default_role = Role.objects.filter(name='owner').first()
            if default_role:
                profile.role = default_role
                profile.set_role_permissions()
                profile.save()
        
        # Log login activity
        log_activity(user, 'login', 'user', user.id, user.username, 'User logged in', request)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'subscription': SubscriptionSerializer(subscription).data,
            'profile': UserProfileSerializer(profile).data
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    # Log logout activity
    log_activity(request.user, 'logout', 'user', request.user.id, request.user.username, 'User logged out', request)
    
    request.user.auth_token.delete()
    return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, CanManageUsers])
def delete_user(request, user_id):
    """Delete a user (admin only)"""
    try:
        user_to_delete = User.objects.get(id=user_id)
        
        # Prevent deleting yourself
        if user_to_delete.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log the deletion
        log_activity(
            request.user,
            'delete',
            'user',
            user_to_delete.id,
            user_to_delete.username,
            f"Deleted user account: {user_to_delete.username}",
            request
        )
        
        username = user_to_delete.username
        user_to_delete.delete()
        
        return Response({
            'message': f'User {username} has been successfully deleted',
            'deleted_user': username
        })
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {'error': f'Failed to delete user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    
    total_customers = Customer.objects.filter(user=user).count()
    total_orders = Order.objects.filter(user=user).count()
    pending_orders = Order.objects.filter(user=user, status='pending').count()
    completed_orders = Order.objects.filter(user=user, status='completed').count()
    
    # Financial stats
    total_revenue = OrderFinancials.objects.filter(order__user=user).aggregate(
        total=Sum('final_price'))['total'] or 0
    total_received = Payment.objects.filter(order__user=user).aggregate(
        total=Sum('amount'))['total'] or 0
    pending_payments = total_revenue - total_received
    
    # Subscription info
    subscription = user.subscription
    
    # Recent activities (last 10)
    recent_activities = ActivityLog.objects.filter(user=user)[:10]
    
    return Response({
        'total_customers': total_customers,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'total_received': total_received,
        'pending_payments': pending_payments,
        'subscription': SubscriptionSerializer(subscription).data,
        'recent_activities': ActivityLogSerializer(recent_activities, many=True).data,
    })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing users"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def users(request):
#     user = request.user
    
#     users = User.objects.filter(is_active=True)
    
#     return Response({
#         'users': users,
#     })

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing activity logs"""
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ActivityLog.objects.filter(user=self.request.user)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing roles"""
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own profile, unless they can manage users
        if hasattr(self.request.user, 'profile') and self.request.user.profile.can_manage_users:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign role to user profile"""
        if not hasattr(request.user, 'profile') or not request.user.profile.can_manage_users:
            return Response(
                {'error': 'You do not have permission to manage users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id)
            profile.role = role
            profile.set_role_permissions()
            profile.save()
            
            log_activity(
                request.user,
                'update',
                'user',
                profile.user.id,
                profile.user.username,
                f"Assigned {role.display_name} role to {profile.user.username}",
                request
            )
            
            return Response({
                'message': f'Role {role.display_name} assigned successfully',
                'profile': UserProfileSerializer(profile).data
            })
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def upgrade(self, request):
        """Upgrade user's subscription plan"""
        new_plan = request.data.get('plan')
        if new_plan not in ['free', 'basic', 'enterprise']:
            return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = request.user.subscription
        subscription.upgrade_plan(new_plan)
        
        return Response({
            'message': f'Successfully upgraded to {new_plan} plan',
            'subscription': SubscriptionSerializer(subscription).data
        })

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel user's subscription"""
        subscription = request.user.subscription
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()
        
        return Response({
            'message': 'Subscription cancelled successfully',
            'subscription': SubscriptionSerializer(subscription).data
        })

    @action(detail=False, methods=['get'])
    def check_limits(self, request):
        """Check current usage against subscription limits"""
        user = request.user
        subscription = user.subscription
        
        current_customers = Customer.objects.filter(user=user).count()
        current_orders = Order.objects.filter(user=user).count()
        current_fabrics = Fabric.objects.filter(user=user).count()
        
        return Response({
            'plan': subscription.plan,
            'customers': {
                'current': current_customers,
                'max': subscription.max_customers,
                'can_add': subscription.can_add_customer(user)
            },
            'orders': {
                'current': current_orders,
                'max': subscription.max_orders,
                'can_add': subscription.can_add_order(user)
            },
            'fabrics': {
                'current': current_fabrics,
                'max': subscription.max_fabrics,
                'can_add': subscription.can_add_fabric(user)
            }
        })


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['first_name', 'created_at']

    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check subscription limits
        if not self.request.user.subscription.can_add_customer(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Customer limit reached for your subscription plan. Please upgrade.')
        
        customer = serializer.save(user=self.request.user)
        
        # Log activity
        log_activity(
            self.request.user, 
            'create', 
            'customer', 
            customer.id, 
            f"{customer.first_name} {customer.last_name}",
            f"Added new customer: {customer.first_name} {customer.last_name}",
            self.request
        )

    def perform_update(self, serializer):
        customer = serializer.save()
        log_activity(
            self.request.user,
            'update',
            'customer',
            customer.id,
            f"{customer.first_name} {customer.last_name}",
            f"Updated customer: {customer.first_name} {customer.last_name}",
            self.request
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'customer',
            instance.id,
            f"{instance.first_name} {instance.last_name}",
            f"Deleted customer: {instance.first_name} {instance.last_name}",
            self.request
        )
        instance.delete()

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        customer = self.get_object()
        orders = Order.objects.filter(customer=customer)
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


class MeasurementViewSet(viewsets.ModelViewSet):
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated, HasPermission]

    def get_queryset(self):
        return Measurement.objects.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer_id = self.request.data.get('customer')
        try:
            customer = Customer.objects.get(id=customer_id, user=self.request.user)
            measurement = serializer.save(customer=customer)
            
            # Log activity
            log_activity(
                self.request.user,
                'create',
                'measurement',
                measurement.id,
                f"{customer.first_name} {customer.last_name}",
                f"Added measurements for {customer.first_name} {customer.last_name}",
                self.request
            )
        except Customer.DoesNotExist:
            raise serializer.ValidationError("Customer not found or you don't have permission.")

    def perform_update(self, serializer):
        measurement = serializer.save()
        customer = measurement.customer
        log_activity(
            self.request.user,
            'update',
            'measurement',
            measurement.id,
            f"{customer.first_name} {customer.last_name}",
            f"Updated measurements for {customer.first_name} {customer.last_name}",
            self.request
        )

    def perform_destroy(self, instance):
        customer = instance.customer
        log_activity(
            self.request.user,
            'delete',
            'measurement',
            instance.id,
            f"{customer.first_name} {customer.last_name}",
            f"Deleted measurements for {customer.first_name} {customer.last_name}",
            self.request
        )
        instance.delete()


class FabricViewSet(viewsets.ModelViewSet):
    serializer_class = FabricSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'fabric_type', 'color', 'supplier']
    ordering_fields = ['name', 'quantity', 'created_at']

    def get_queryset(self):
        return Fabric.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check subscription limits
        if not self.request.user.subscription.can_add_fabric(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Fabric limit reached for your subscription plan. Please upgrade.')
        
        fabric = serializer.save(user=self.request.user)
        
        # Log activity
        log_activity(
            self.request.user,
            'create',
            'fabric',
            fabric.id,
            fabric.name,
            f"Added new fabric: {fabric.name} - {fabric.color}",
            self.request
        )

    def perform_update(self, serializer):
        fabric = serializer.save()
        log_activity(
            self.request.user,
            'update',
            'fabric',
            fabric.id,
            fabric.name,
            f"Updated fabric: {fabric.name} - {fabric.color}",
            self.request
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'fabric',
            instance.id,
            instance.name,
            f"Deleted fabric: {instance.name} - {instance.color}",
            self.request
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        threshold = float(request.query_params.get('threshold', 5))
        fabrics = self.get_queryset().filter(quantity__lte=threshold)
        serializer = self.get_serializer(fabrics, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name']
    ordering_fields = ['order_date', 'due_date', 'status']

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        # Check subscription limits
        if not self.request.user.subscription.can_add_order(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Order limit reached for your subscription plan. Please upgrade.')
        
        order = serializer.save(user=self.request.user)
        
        # Log activity
        log_activity(
            self.request.user,
            'create',
            'order',
            order.id,
            order.order_number,
            f"Created order {order.order_number} for {order.customer.first_name} {order.customer.last_name}",
            self.request
        )

    def perform_update(self, serializer):
        order = serializer.save()
        log_activity(
            self.request.user,
            'update',
            'order',
            order.id,
            order.order_number,
            f"Updated order {order.order_number}",
            self.request
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'order',
            instance.id,
            instance.order_number,
            f"Deleted order {instance.order_number}",
            self.request
        )
        instance.delete()

    def perform_destroy(self, instance):
        customer = instance.customer
        log_activity(
            self.request.user,
            'delete',
            'measurement',
            instance.id,
            f"{customer.first_name} {customer.last_name}",
            f"Deleted measurements for {customer.first_name} {customer.last_name}",
            self.request
        )
        instance.delete()


class FabricViewSet(viewsets.ModelViewSet):
    serializer_class = FabricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'fabric_type', 'color', 'supplier']
    ordering_fields = ['name', 'quantity', 'created_at']

    def get_queryset(self):
        return Fabric.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check subscription limits
        if not self.request.user.subscription.can_add_fabric(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Fabric limit reached for your subscription plan. Please upgrade.')
        
        fabric = serializer.save(user=self.request.user)
        
        # Log activity
        log_activity(
            self.request.user,
            'create',
            'fabric',
            fabric.id,
            fabric.name,
            f"Added new fabric: {fabric.name} - {fabric.color}",
            self.request
        )

    def perform_update(self, serializer):
        fabric = serializer.save()
        log_activity(
            self.request.user,
            'update',
            'fabric',
            fabric.id,
            fabric.name,
            f"Updated fabric: {fabric.name} - {fabric.color}",
            self.request
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'fabric',
            instance.id,
            instance.name,
            f"Deleted fabric: {instance.name} - {instance.color}",
            self.request
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        threshold = float(request.query_params.get('threshold', 5))
        fabrics = self.get_queryset().filter(quantity__lte=threshold)
        serializer = self.get_serializer(fabrics, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name']
    ordering_fields = ['order_date', 'due_date', 'status']

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        # Check subscription limits
        if not self.request.user.subscription.can_add_order(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Order limit reached for your subscription plan. Please upgrade.')
        
        order = serializer.save(user=self.request.user)
        
        # Log activity
        log_activity(
            self.request.user,
            'create',
            'order',
            order.id,
            order.order_number,
            f"Created order {order.order_number} for {order.customer.first_name} {order.customer.last_name}",
            self.request
        )

    def perform_update(self, serializer):
        order = serializer.save()
        log_activity(
            self.request.user,
            'update',
            'order',
            order.id,
            order.order_number,
            f"Updated order {order.order_number}",
            self.request
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'order',
            instance.id,
            instance.order_number,
            f"Deleted order {instance.order_number}",
            self.request
        )
        instance.delete()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response({'status': 'Status updated successfully'})
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, HasPermission]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)

    def perform_create(self, serializer):
        order_id = self.request.data.get('order')
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
            payment = serializer.save()
            
            # Log activity
            log_activity(
                self.request.user,
                'create',
                'payment',
                payment.id,
                f"₦{payment.amount}",
                f"Recorded payment of ₦{payment.amount} for order {order.order_number}",
                self.request
            )
            
            # Update fabric quantity if used
            if order.fabric and order.fabric_quantity_used:
                order.fabric.quantity -= order.fabric_quantity_used
                order.fabric.save()
                
        except Order.DoesNotExist:
            raise serializer.ValidationError("Order not found or you don't have permission.")

    def perform_destroy(self, instance):
        log_activity(
            self.request.user,
            'delete',
            'payment',
            instance.id,
            f"₦{instance.amount}",
            f"Deleted payment of ₦{instance.amount}",
            self.request
        )
        instance.delete()


class OrderFinancialsViewSet(viewsets.ModelViewSet):
    serializer_class = OrderFinancialsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderFinancials.objects.filter(order__user=self.request.user)

    def perform_create(self, serializer):
        order_id = self.request.data.get('order')
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
            serializer.save()
        except Order.DoesNotExist:
            raise serializer.ValidationError("Order not found or you don't have permission.")

