from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, Measurement, Fabric, Order, Payment, OrderFinancials, Subscription,ActivityLog,UserProfile,Role
from datetime import datetime, timedelta

# An aware datetime
aware_dt = datetime.fromisoformat("2025-10-05T14:00:00+02:00")

# A naive datetime
naive_dt = datetime.now()

# Make the naive datetime aware to perform the conversion
naive_dt_utc = naive_dt.replace(tzinfo=aware_dt.tzinfo)

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'display_name', 'description']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display = serializers.CharField(source='role.display_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'role_name', 'role_display', 'phone', 'address', 
                  'avatar', 'bio', 'can_manage_users', 'can_manage_customers', 
                  'can_manage_orders', 'can_manage_payments', 'can_manage_fabrics', 
                  'can_manage_measurements', 'can_view_reports', 'can_manage_settings',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 'email', 'phone', 
                  'address', 'measurements', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class FabricSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Fabric
        fields = ['id', 'user', 'name', 'fabric_type', 'color', 'quantity', 
                  'price_per_unit', 'supplier', 'description', 'image', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'payment_method', 'payment_date', 
                  'transaction_reference', 'notes', 'created_at']
        read_only_fields = ['id', 'payment_date', 'created_at']


class OrderFinancialsSerializer(serializers.ModelSerializer):
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = OrderFinancials
        fields = ['id', 'order', 'material_cost', 'labor_cost', 'additional_cost', 
                  'total_cost', 'quoted_price', 'discount', 'final_price', 
                  'amount_paid', 'balance', 'payment_status']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    financials = OrderFinancialsSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'customer', 'customer_name', 'order_number', 
                  'garment_type', 'status', 'measurement', 'fabric', 
                  'fabric_quantity_used', 'order_date', 'due_date', 'delivery_date', 
                  'description', 'special_instructions', 'design_image', 
                  'payments', 'financials', 'created_at', 'updated_at', 'total_amount', 'amount_paid']
        read_only_fields = ['id', 'user', 'order_number', 'order_date', 'created_at', 'updated_at']


class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    amount_paid = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer', 'customer_name', 'garment_type', 
                  'status', 'order_date', 'due_date', 'total_amount', 'amount_paid']

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"

    def get_total_amount(self, obj):
        if hasattr(obj, 'financials'):
            return obj.financials.final_price
        return None

    def get_amount_paid(self, obj):
        if hasattr(obj, 'financials'):
            return obj.financials.amount_paid
        return 0


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=['owner', 'manager', 'tailor', 'assistant', 'viewer'], required=False, default='owner')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        role_name = validated_data.pop('role', 'owner')
        
        user = User.objects.create_user(**validated_data)
        
        # Create default free subscription
        subscription = Subscription.objects.create(
            user=user,
            plan='free',
            status='active'
        )
        subscription.set_plan_limits()
        subscription.save()
        
        # Create user profile with role
        role = Role.objects.filter(name=role_name).first()
        profile = UserProfile.objects.create(user=user, role=role)
        if role:
            profile.set_role_permissions()
            profile.save()
        
        return user
    
class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'status', 'start_date', 'end_date', 
                  'is_trial', 'auto_renew', 'max_customers', 'max_orders', 
                  'max_fabrics', 'is_active', 'days_remaining', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'start_date', 'created_at', 'updated_at']

    def get_days_remaining(self, obj):
        if obj.end_date:
            delta = obj.end_date - naive_dt_utc
            return max(0, delta.days)
        return None
    
class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'action', 'resource_type', 'resource_id', 
                  'resource_name', 'description', 'created_at', 'ip_address']
        read_only_fields = ['id', 'user', 'created_at']    