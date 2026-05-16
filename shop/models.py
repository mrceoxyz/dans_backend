from django.db import models
from django.contrib.auth.models import User, Group, Permission
from datetime import datetime, timedelta

# An aware datetime
aware_dt = datetime.fromisoformat("2025-10-05T14:00:00+02:00")

# A naive datetime
naive_dt = datetime.now()

# Make the naive datetime aware to perform the conversion
naive_dt_utc = naive_dt.replace(tzinfo=aware_dt.tzinfo)

class Role(models.Model):
    """Custom roles for the tailor shop"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('tailor', 'Tailor'),
        ('assistant', 'Assistant'),
        ('viewer', 'Viewer'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class UserProfile(models.Model):
    """Extended user profile with role and permissions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    # Permissions
    can_manage_users = models.BooleanField(default=False)
    can_manage_customers = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=True)
    can_manage_payments = models.BooleanField(default=False)
    can_manage_fabrics = models.BooleanField(default=True)
    can_manage_measurements = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.display_name if self.role else 'No Role'}"
    
    def set_role_permissions(self):
        """Set permissions based on role"""
        if not self.role:
            return
        
        if self.role.name == 'owner':
            self.can_manage_users = True
            self.can_manage_customers = True
            self.can_manage_orders = True
            self.can_manage_payments = True
            self.can_manage_fabrics = True
            self.can_manage_measurements = True
            self.can_view_reports = True
            self.can_manage_settings = True
        elif self.role.name == 'manager':
            self.can_manage_users = False
            self.can_manage_customers = True
            self.can_manage_orders = True
            self.can_manage_payments = True
            self.can_manage_fabrics = True
            self.can_manage_measurements = True
            self.can_view_reports = True
            self.can_manage_settings = False
        elif self.role.name == 'tailor':
            self.can_manage_users = False
            self.can_manage_customers = True
            self.can_manage_orders = True
            self.can_manage_payments = False
            self.can_manage_fabrics = False
            self.can_manage_measurements = True
            self.can_view_reports = False
            self.can_manage_settings = False
        elif self.role.name == 'assistant':
            self.can_manage_users = False
            self.can_manage_customers = True
            self.can_manage_orders = False
            self.can_manage_payments = False
            self.can_manage_fabrics = False
            self.can_manage_measurements = True
            self.can_view_reports = False
            self.can_manage_settings = False
        elif self.role.name == 'viewer':
            self.can_manage_users = False
            self.can_manage_customers = False
            self.can_manage_orders = False
            self.can_manage_payments = False
            self.can_manage_fabrics = False
            self.can_manage_measurements = False
            self.can_view_reports = True
            self.can_manage_settings = False


# Signal to auto-create user profile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
    ]
    
    RESOURCE_CHOICES = [
        ('customer', 'Customer'),
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('fabric', 'Fabric'),
        ('measurement', 'Measurement'),
        ('user', 'User'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_CHOICES)
    resource_id = models.IntegerField(null=True, blank=True)
    resource_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.resource_type} - {self.resource_name}"
    



class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Measurement(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='measurements')
    measurement_date = models.DateField(auto_now_add=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Upper body measurements (in inches or cm)
    neck = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    chest = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hips = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    shoulder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sleeve_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    arm_hole = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wrist = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Lower body measurements
    inseam = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    outseam = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    thigh = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    knee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ankle = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lap = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Other measurements
    back_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    front_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    agbada_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    agbada_width = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-measurement_date']

    def __str__(self):
        return f"{self.customer.first_name} {self.customer.last_name} - {self.measurement_date}"


class Fabric(models.Model):
    FABRIC_TYPE_CHOICES = [
        ('cotton', 'Cotton'),
        ('silk', 'Silk'),
        ('wool', 'Wool'),
        ('linen', 'Linen'),
        ('polyester', 'Polyester'),
        ('chiffon', 'Chiffon'),
        ('velvet', 'Velvet'),
        ('denim', 'Denim'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fabrics')
    name = models.CharField(max_length=200)
    fabric_type = models.CharField(max_length=50, choices=FABRIC_TYPE_CHOICES)
    color = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity in meters/yards")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='fabrics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.color}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('measuring', 'Taking Measurements'),
        ('cutting', 'Cutting'),
        ('stitching', 'Stitching'),
        ('fitting', 'Fitting'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    GARMENT_TYPE_CHOICES = [
        ('shirt', 'Shirt'),
        ('babbar riga', 'Babbar Riga'),
        ('kaftan', 'Kaftan'),
        ('jallabiyya', 'Jallabiyya'),
        ('trouser', 'Trouser'),
        ('suit', 'Suit'),
        ('dress', 'Dress'),
        ('blouse', 'Blouse'),
        ('skirt', 'Skirt'),
        ('coat', 'Coat'),
        ('traditional', 'Traditional Wear'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    garment_type = models.CharField(max_length=50, choices=GARMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    measurement = models.ForeignKey(Measurement, on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True, blank=True)
    fabric_quantity_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    order_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    
    description = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    design_image = models.ImageField(upload_to='designs/', blank=True, null=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.customer.first_name} {self.customer.last_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime
            prefix = 'ORD'
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__startswith=f'{prefix}{date_str}').order_by('-order_number').first()
            if last_order:
                last_number = int(last_order.order_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.order_number = f'{prefix}{date_str}{new_number:04d}'
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_reference = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.amount} for {self.order.order_number}"


class OrderFinancials(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='financials')
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def amount_paid(self):
        return sum(payment.amount for payment in self.order.payments.all())
    
    @property
    def balance(self):
        return self.final_price - self.amount_paid
    
    @property
    def payment_status(self):
        if self.amount_paid == 0:
            return 'pending'
        elif self.amount_paid < self.final_price:
            return 'partial'
        else:
            return 'paid'

    def __str__(self):
        return f"Financials for {self.order.order_number}"
    

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_trial = models.BooleanField(default=False)
    auto_renew = models.BooleanField(default=False)
    
    # Plan limits
    max_customers = models.IntegerField(default=10)  # Free: 10, Basic: 100, Enterprise: unlimited
    max_orders = models.IntegerField(default=20)  # Free: 20, Basic: 500, Enterprise: unlimited
    max_fabrics = models.IntegerField(default=15)  # Free: 15, Basic: 200, Enterprise: unlimited
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

    def is_active(self):
        if self.status != 'active':
            return False
        if self.end_date and naive_dt_utc > self.end_date:
            self.status = 'expired'
            self.save()
            return False
        return True

    def set_plan_limits(self):
        """Set limits based on plan type"""
        if self.plan == 'free':
            self.max_customers = 10
            self.max_orders = 20
            self.max_fabrics = 15
        elif self.plan == 'basic':
            self.max_customers = 100
            self.max_orders = 500
            self.max_fabrics = 200
        elif self.plan == 'enterprise':
            self.max_customers = 999999  # Unlimited
            self.max_orders = 999999
            self.max_fabrics = 999999

    def upgrade_plan(self, new_plan):
        """Upgrade subscription plan"""
        self.plan = new_plan
        self.set_plan_limits()
        if new_plan != 'free':
            self.end_date = naive_dt_utc + timedelta(days=30)
        self.save()

    def can_add_customer(self, user):
        """Check if user can add more customers"""
        from .models import Customer
        current_count = Customer.objects.filter(user=user).count()
        return current_count < self.max_customers

    def can_add_order(self, user):
        """Check if user can add more orders"""
        from .models import Order
        current_count = Order.objects.filter(user=user).count()
        return current_count < self.max_orders

    def can_add_fabric(self, user):
        """Check if user can add more fabrics"""
        from .models import Fabric
        current_count = Fabric.objects.filter(user=user).count()
        return current_count < self.max_fabrics