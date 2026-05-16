from django.contrib import admin
from .models import Customer, Measurement, Fabric, Order, Payment, OrderFinancials, Subscription, ActivityLog, Role, UserProfile

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'created_at']
    search_fields = ['name', 'display_name']
    filter_horizontal = ['permissions']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'can_manage_users', 'can_manage_orders', 'can_manage_payments', 'created_at']
    list_filter = ['role', 'can_manage_users', 'can_manage_orders']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'phone', 'address', 'avatar', 'bio')
        }),
        ('Permissions', {
            'fields': ('can_manage_users', 'can_manage_customers', 'can_manage_orders',
                      'can_manage_payments', 'can_manage_fabrics', 'can_manage_measurements',
                      'can_view_reports', 'can_manage_settings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'resource_name', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['user__username', 'resource_name', 'description']
    readonly_fields = ['user', 'action', 'resource_type', 'resource_id', 'resource_name', 'description', 'ip_address', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False    

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'is_active', 'auto_renew']
    list_filter = ['plan', 'status', 'is_trial', 'auto_renew']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['start_date', 'created_at', 'updated_at']
    
    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'user', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_filter = ['created_at', 'user']


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['customer', 'gender', 'measurement_date', 'created_at']
    search_fields = ['customer__first_name', 'customer__last_name']
    list_filter = ['gender', 'measurement_date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = ['name', 'fabric_type', 'color', 'quantity', 'price_per_unit', 'user', 'created_at']
    search_fields = ['name', 'color', 'supplier']
    list_filter = ['fabric_type', 'created_at', 'user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'garment_type', 'status', 'order_date', 'due_date', 'user']
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name']
    list_filter = ['status', 'garment_type', 'order_date', 'user']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'order_date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_method', 'payment_date', 'transaction_reference']
    search_fields = ['order__order_number', 'transaction_reference']
    list_filter = ['payment_method', 'payment_date']
    readonly_fields = ['payment_date', 'created_at']
    date_hierarchy = 'payment_date'


@admin.register(OrderFinancials)
class OrderFinancialsAdmin(admin.ModelAdmin):
    list_display = ['order', 'total_cost', 'quoted_price', 'final_price', 'get_amount_paid', 'get_balance']
    search_fields = ['order__order_number']
    readonly_fields = ['get_amount_paid', 'get_balance', 'get_payment_status']

    def get_amount_paid(self, obj):
        return obj.amount_paid
    get_amount_paid.short_description = 'Amount Paid'

    def get_balance(self, obj):
        return obj.balance
    get_balance.short_description = 'Balance'

    def get_payment_status(self, obj):
        return obj.payment_status
    get_payment_status.short_description = 'Payment Status'