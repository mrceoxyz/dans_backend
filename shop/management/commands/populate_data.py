# populate_data.py
# Run this script with: python manage.py shell < populate_data.py

from django.contrib.auth.models import User
from shop.models import Customer, Measurement, Fabric, Order, Payment, OrderFinancials, Subscription, Role, UserProfile
from decimal import Decimal
from datetime import datetime, timedelta
import random

print("Starting data population...")
print("="*60)

# Step 1: Initialize Roles
print("\n[1/9] Creating Roles...")
roles_data = [
    {'name': 'owner', 'display_name': 'Owner', 'description': 'Full access to all features including user management and settings'},
    {'name': 'manager', 'display_name': 'Manager', 'description': 'Can manage customers, orders, payments, and view reports'},
    {'name': 'tailor', 'display_name': 'Tailor', 'description': 'Can manage orders, customers, and measurements'},
    {'name': 'assistant', 'display_name': 'Assistant', 'description': 'Can add customers and measurements only'},
    {'name': 'viewer', 'display_name': 'Viewer', 'description': 'Read-only access to reports and data'},
]

roles = {}
for role_data in roles_data:
    role, created = Role.objects.get_or_create(
        name=role_data['name'],
        defaults={
            'display_name': role_data['display_name'],
            'description': role_data['description']
        }
    )
    roles[role_data['name']] = role
    if created:
        print(f"  ✓ Created role: {role.display_name}")
    else:
        print(f"  → Role already exists: {role.display_name}")

# Step 2: Create Users with Different Roles
print("\n[2/9] Creating Users with Roles...")
users_data = [
    {'username': 'owner1', 'email': 'owner@shop.com', 'first_name': 'Ahmed', 'last_name': 'Ibrahim', 'password': 'password123', 'role': 'owner'},
    {'username': 'manager1', 'email': 'manager@shop.com', 'first_name': 'Fatima', 'last_name': 'Yusuf', 'password': 'password123', 'role': 'manager'},
    {'username': 'tailor1', 'email': 'tailor@shop.com', 'first_name': 'Musa', 'last_name': 'Abubakar', 'password': 'password123', 'role': 'tailor'},
    {'username': 'assistant1', 'email': 'assistant@shop.com', 'first_name': 'Zainab', 'last_name': 'Hassan', 'password': 'password123', 'role': 'assistant'},
]

users = []
for user_data in users_data:
    role_name = user_data.pop('role')
    password = user_data.pop('password')
    
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults=user_data
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"  ✓ Created user: {user.username} ({user.first_name} {user.last_name})")
    else:
        print(f"  → User already exists: {user.username}")
    
    users.append(user)
    
    # Create or update user profile with role
    profile, profile_created = UserProfile.objects.get_or_create(user=user)
    profile.role = roles[role_name]
    profile.set_role_permissions()
    profile.save()
    
    if profile_created:
        print(f"     ✓ Created profile with role: {roles[role_name].display_name}")
    else:
        print(f"     → Updated profile role to: {roles[role_name].display_name}")

# Step 3: Create or Update Subscriptions
print("\n[3/9] Creating Subscriptions...")
subscription_plans = ['free', 'basic', 'enterprise', 'free']

for i, user in enumerate(users):
    plan = subscription_plans[i % len(subscription_plans)]
    
    subscription, created = Subscription.objects.get_or_create(
        user=user,
        defaults={
            'plan': plan,
            'status': 'active',
            'is_trial': False if plan == 'free' else True,
            'auto_renew': False if plan == 'free' else True,
        }
    )
    
    if not created:
        subscription.plan = plan
        subscription.status = 'active'
        subscription.is_trial = False if plan == 'free' else True
        subscription.auto_renew = False if plan == 'free' else True
    
    subscription.set_plan_limits()
    
    if plan != 'free':
        subscription.end_date = datetime.now() + timedelta(days=30)
    else:
        subscription.end_date = None
    
    subscription.save()
    
    if created:
        print(f"  ✓ Created {plan.upper()} subscription for {user.username}")
    else:
        print(f"  → Updated {plan.upper()} subscription for {user.username}")
    
    print(f"     Limits: {subscription.max_customers} customers, {subscription.max_orders} orders, {subscription.max_fabrics} fabrics")

# Step 4: Create Customers
print("\n[4/9] Creating Customers...")
customers_data = [
    {'first_name': 'Musa', 'last_name': 'Abubakar', 'email': 'musa.abubakar@email.com', 'phone': '+234 803 123 4567', 'address': '12 Zaria Road, Kano'},
    {'first_name': 'Aisha', 'last_name': 'Mohammed', 'email': 'aisha.mohammed@email.com', 'phone': '+234 805 234 5678', 'address': '45 Maiduguri Road, Kano'},
    {'first_name': 'Ibrahim', 'last_name': 'Sani', 'email': 'ibrahim.sani@email.com', 'phone': '+234 807 345 6789', 'address': '78 Hadejia Road, Kano'},
    {'first_name': 'Hauwa', 'last_name': 'Bello', 'email': 'hauwa.bello@email.com', 'phone': '+234 809 456 7890', 'address': '23 Zoo Road, Kano'},
    {'first_name': 'Yusuf', 'last_name': 'Garba', 'email': 'yusuf.garba@email.com', 'phone': '+234 811 567 8901', 'address': '56 Ahmadu Bello Way, Kano'},
    {'first_name': 'Zainab', 'last_name': 'Hassan', 'email': 'zainab.hassan@email.com', 'phone': '+234 813 678 9012', 'address': '89 Ibrahim Taiwo Road, Kano'},
    {'first_name': 'Abdullahi', 'last_name': 'Usman', 'email': 'abdullahi.usman@email.com', 'phone': '+234 815 789 0123', 'address': '34 France Road, Kano'},
    {'first_name': 'Amina', 'last_name': 'Aliyu', 'email': 'amina.aliyu@email.com', 'phone': '+234 817 890 1234', 'address': '67 Kofar Ruwa, Kano'},
    {'first_name': 'Umar', 'last_name': 'Danjuma', 'email': 'umar.danjuma@email.com', 'phone': '+234 819 901 2345', 'address': '90 Katsina Road, Kano'},
    {'first_name': 'Halima', 'last_name': 'Bala', 'email': 'halima.bala@email.com', 'phone': '+234 821 012 3456', 'address': '45 Gwarzo Road, Kano'},
]

customers = []
for i, customer_data in enumerate(customers_data):
    customer, created = Customer.objects.get_or_create(
        email=customer_data['email'],
        defaults={
            **customer_data,
            'user': users[i % len(users)]
        }
    )
    if created:
        print(f"  ✓ Created customer: {customer.first_name} {customer.last_name} (assigned to {customer.user.username})")
    else:
        print(f"  → Customer already exists: {customer.first_name} {customer.last_name}")
    customers.append(customer)

# Step 5: Create Measurements
print("\n[5/9] Creating Measurements...")
male_names = ['Musa', 'Ibrahim', 'Yusuf', 'Abdullahi', 'Umar']
measurement_count = 0

for customer in customers:
    if customer.first_name in male_names:
        measurement, created = Measurement.objects.get_or_create(
            customer=customer,
            defaults={
                'gender': 'M',
                'neck': Decimal(random.uniform(14.5, 17.0)),
                'chest': Decimal(random.uniform(38.0, 44.0)),
                'waist': Decimal(random.uniform(32.0, 40.0)),
                'shoulder': Decimal(random.uniform(16.0, 19.0)),
                'sleeve_length': Decimal(random.uniform(24.0, 26.0)),
                'inseam': Decimal(random.uniform(30.0, 34.0)),
                'outseam': Decimal(random.uniform(40.0, 44.0)),
                'notes': 'Regular fit preferred'
            }
        )
    else:
        measurement, created = Measurement.objects.get_or_create(
            customer=customer,
            defaults={
                'gender': 'F',
                'neck': Decimal(random.uniform(13.0, 15.0)),
                'chest': Decimal(random.uniform(34.0, 40.0)),
                'waist': Decimal(random.uniform(26.0, 34.0)),
                'hips': Decimal(random.uniform(36.0, 44.0)),
                'shoulder': Decimal(random.uniform(14.0, 17.0)),
                'sleeve_length': Decimal(random.uniform(22.0, 24.0)),
                'back_length': Decimal(random.uniform(15.0, 17.0)),
                'notes': 'Fitted style preferred'
            }
        )
    if created:
        measurement_count += 1

print(f"  ✓ Created {measurement_count} measurements")

# Step 6: Create Fabrics
print("\n[6/9] Creating Fabrics...")
fabrics_data = [
    {'name': 'Premium Cotton White', 'fabric_type': 'cotton', 'color': 'White', 'quantity': Decimal('50.00'), 'price_per_unit': Decimal('1500.00'), 'supplier': 'Kano Textiles Ltd'},
    {'name': 'Blue Denim', 'fabric_type': 'denim', 'color': 'Blue', 'quantity': Decimal('30.00'), 'price_per_unit': Decimal('2000.00'), 'supplier': 'Northern Fabrics'},
    {'name': 'Black Wool Blend', 'fabric_type': 'wool', 'color': 'Black', 'quantity': Decimal('25.00'), 'price_per_unit': Decimal('3500.00'), 'supplier': 'Premium Textiles'},
    {'name': 'Floral Chiffon', 'fabric_type': 'chiffon', 'color': 'Multi-color', 'quantity': Decimal('40.00'), 'price_per_unit': Decimal('2500.00'), 'supplier': 'Fashion Fabrics'},
    {'name': 'Navy Linen', 'fabric_type': 'linen', 'color': 'Navy Blue', 'quantity': Decimal('35.00'), 'price_per_unit': Decimal('1800.00'), 'supplier': 'Kano Textiles Ltd'},
    {'name': 'Red Velvet', 'fabric_type': 'velvet', 'color': 'Red', 'quantity': Decimal('20.00'), 'price_per_unit': Decimal('4000.00'), 'supplier': 'Premium Textiles'},
    {'name': 'Grey Polyester', 'fabric_type': 'polyester', 'color': 'Grey', 'quantity': Decimal('60.00'), 'price_per_unit': Decimal('1200.00'), 'supplier': 'Budget Fabrics'},
    {'name': 'Green Silk', 'fabric_type': 'silk', 'color': 'Emerald Green', 'quantity': Decimal('15.00'), 'price_per_unit': Decimal('5000.00'), 'supplier': 'Luxury Textiles'},
    {'name': 'Brown Cotton', 'fabric_type': 'cotton', 'color': 'Brown', 'quantity': Decimal('45.00'), 'price_per_unit': Decimal('1400.00'), 'supplier': 'Northern Fabrics'},
    {'name': 'Pink Chiffon', 'fabric_type': 'chiffon', 'color': 'Pink', 'quantity': Decimal('3.00'), 'price_per_unit': Decimal('2600.00'), 'supplier': 'Fashion Fabrics', 'description': 'Low stock alert'},
]

fabrics = []
fabric_count = 0
for fabric_data in fabrics_data:
    fabric, created = Fabric.objects.get_or_create(
        name=fabric_data['name'],
        user=users[0],  # Assign to owner
        defaults=fabric_data
    )
    if created:
        fabric_count += 1
        low_stock = " [LOW STOCK]" if fabric.quantity <= 5 else ""
        print(f"  ✓ Created fabric: {fabric.name} - {fabric.color}{low_stock}")
    fabrics.append(fabric)

print(f"  → Total fabrics: {len(fabrics)} ({fabric_count} new)")

# Step 7: Create Orders
print("\n[7/9] Creating Orders...")
garment_types = ['shirt', 'trouser', 'suit', 'dress', 'blouse', 'skirt', 'traditional']
statuses = ['pending', 'measuring', 'cutting', 'stitching', 'fitting', 'completed', 'delivered']

orders = []
order_count = 0
for i, customer in enumerate(customers[:8]):  # Create orders for first 8 customers
    num_orders = random.randint(1, 2)
    for j in range(num_orders):
        order_date = datetime.now().date() - timedelta(days=random.randint(1, 60))
        due_date = order_date + timedelta(days=random.randint(7, 21))
        
        garment = random.choice(garment_types)
        status = random.choice(statuses[:6])  # Avoid too many delivered
        
        measurement = Measurement.objects.filter(customer=customer).first()
        fabric = random.choice(fabrics)
        
        order = Order.objects.create(
            user=customer.user,
            customer=customer,
            garment_type=garment,
            status=status,
            measurement=measurement,
            fabric=fabric,
            fabric_quantity_used=Decimal(random.uniform(2.0, 5.0)),
            due_date=due_date,
            description=f"Custom {garment} for {customer.first_name}",
            special_instructions="Handle with care, customer preference noted"
        )
        Order.objects.filter(id=order.id).update(order_date=order_date)
        
        order_count += 1
        orders.append(order)

print(f"  ✓ Created {order_count} orders")

# Step 8: Create Financials and Payments
print("\n[8/9] Creating Order Financials and Payments...")
financial_count = 0
payment_count = 0
payment_methods = ['cash', 'bank_transfer', 'card', 'mobile_money']

for order in orders:
    # Create financials
    material_cost = Decimal(random.uniform(5000, 15000))
    labor_cost = Decimal(random.uniform(8000, 20000))
    additional_cost = Decimal(random.uniform(0, 3000))
    total_cost = material_cost + labor_cost + additional_cost
    quoted_price = total_cost * Decimal('1.4')
    discount = Decimal(0) if random.random() > 0.3 else Decimal(random.uniform(500, 2000))
    final_price = quoted_price - discount
    
    financial, created = OrderFinancials.objects.get_or_create(
        order=order,
        defaults={
            'material_cost': material_cost,
            'labor_cost': labor_cost,
            'additional_cost': additional_cost,
            'total_cost': total_cost,
            'quoted_price': quoted_price,
            'discount': discount,
            'final_price': final_price
        }
    )
    if created:
        financial_count += 1
    
    # Create payments (70% of orders have payments)
    if random.random() < 0.7:
        if random.random() < 0.5:
            # Full payment
            payment = Payment.objects.create(
                order=order,
                amount=final_price,
                payment_method=random.choice(payment_methods),
                transaction_reference=f"TXN{random.randint(100000, 999999)}",
                notes="Full payment received"
            )
            payment_count += 1
        else:
            # Partial payments
            num_payments = random.randint(1, 2)
            remaining = final_price
            for k in range(num_payments):
                amount = Decimal(random.uniform(float(final_price * Decimal('0.3')), float(final_price * Decimal('0.6'))))
                if amount > remaining:
                    amount = remaining
                
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=random.choice(payment_methods),
                    transaction_reference=f"TXN{random.randint(100000, 999999)}",
                    notes=f"Partial payment {k+1}"
                )
                remaining -= amount
                payment_count += 1

print(f"  ✓ Created {financial_count} order financials")
print(f"  ✓ Created {payment_count} payments")

# Step 9: Summary
print("\n[9/9] Summary")
print("="*60)
print(f"✓ Roles:            {Role.objects.count()}")
print(f"✓ Users:            {User.objects.count()}")
print(f"✓ User Profiles:    {UserProfile.objects.count()}")
print(f"✓ Subscriptions:    {Subscription.objects.count()}")
print(f"✓ Customers:        {Customer.objects.count()}")
print(f"✓ Measurements:     {Measurement.objects.count()}")
print(f"✓ Fabrics:          {Fabric.objects.count()}")
print(f"✓ Orders:           {Order.objects.count()}")
print(f"✓ Financials:       {OrderFinancials.objects.count()}")
print(f"✓ Payments:         {Payment.objects.count()}")

print("\n" + "="*60)
print("🎉 Sample data population completed successfully!")
print("="*60)

print("\n📋 User Accounts & Roles:")
print("-" * 60)
for user in users:
    profile = user.profile
    subscription = user.subscription
    print(f"Username: {user.username:12} | Password: password123")
    print(f"  Role: {profile.role.display_name:15} | Plan: {subscription.plan.upper()}")
    print(f"  Name: {user.first_name} {user.last_name}")
    print(f"  Permissions:")
    print(f"    - Manage Users:    {profile.can_manage_users}")
    print(f"    - Manage Orders:   {profile.can_manage_orders}")
    print(f"    - Manage Payments: {profile.can_manage_payments}")
    print("-" * 60)

print("\n💡 Test different permission levels by logging in with different users!")
print("   Each user has a different role with specific permissions.\n")