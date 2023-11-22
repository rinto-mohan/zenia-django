from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from datetime import date

# from razorpay import PaymentLink

# Create your models here.
class User_manager(BaseUserManager):
    def create_user(self, email, username,first_name,last_name,mobile, password):
        if not email:
            raise ValueError('User must have an email address')
        
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            mobile=mobile
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username,first_name,last_name, mobile, password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            username = username,
            first_name=first_name,
            last_name=last_name,
            mobile = mobile
        )

        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)

    


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    mobile = models.CharField(max_length=10, unique=True)
    profile_img = models.ImageField(upload_to='photos/categories',blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','mobile','first_name','last_name']

    objects = User_manager()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True



class Category(models.Model):
    category_name = models.CharField(max_length=20, unique=True)
    description = models.TextField(max_length=100,blank= True)
    is_available = models.BooleanField(default=True)
    soft_deleted = models.BooleanField(default=False)
    category_image = models.ImageField(upload_to='photos/categories',blank=True)
    
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_name

class Product(models.Model):
    product_name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.CharField(max_length=200,blank=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.1)
    quantity = models.IntegerField()
    is_available = models.BooleanField(default=True)
    soft_deleted = models.BooleanField(default=False)
    product_images = models.ImageField(upload_to='photos/products')
    product_images_1 = models.ImageField(upload_to='photos/products',blank=True)
    product_images_2 = models.ImageField(upload_to='photos/products',blank=True)
    product_images_3 = models.ImageField(upload_to='photos/products',blank=True)
    starred = models.BooleanField(default=False)

    def __str__(self):
           return self.product_name
    
class Address(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50,blank=False, default='')
    city = models.CharField(max_length=50,blank=False, default='')
    address_1 = models.CharField(max_length=500,blank=False)
    address_2 = models.CharField(max_length=500,blank=False, default='')
    STATE_CHOICES = (
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Delhi', 'Delhi'),
    ('Puducherry', 'Puducherry'),
    )
    state = models.CharField(max_length=100, choices=STATE_CHOICES, blank=False, default='')
    pin = models.IntegerField()
    mobile_number = models.CharField(max_length=10, blank=False, default='')
    is_billing = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_billing:
            Address.objects.filter(user_id=self.user_id).exclude(id=self.id).update(is_billing=False)
        super(Address, self).save(*args, **kwargs)

    def __str__(self):
        return self.address_1
    
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(blank=True, max_digits=10, decimal_places=2)
    expiration_date = models.DateField()
    is_active = models.BooleanField(default=True)
    # applied = models.BooleanField(default=False,blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.IntegerField( blank=True, default=1 )
    description = models.TextField(max_length=500, blank=True)
    COUPON_CHOICES = (
        ("percentage", "percentage"),
        ("fixed", "fixed"),
    )
    coupon_type = models.CharField(max_length=50, choices=COUPON_CHOICES, default=("percentage", "percentage"))


    def __str__(self):
        return self.code
    
    def is_used_by_user(self, user):
        redeemed_details = UserCoupons.objects.filter(coupon=self, user=user, is_used=True)
        return redeemed_details.exists()


    
default_expiration_date = date(9999, 12, 31)
    
default_coupon, created = Coupon.objects.get_or_create(
    code="DEFAULT_COUPON",
    defaults={
        "discount": 0,
        "is_active": True,
        "expiration_date": default_expiration_date,
        "min_price": 0,
        "max_uses": 1,
        "description": "No coupon applied",
        "coupon_type": "percentage",
    }
)
if not created:
    default_coupon.expiration_date = default_expiration_date
    default_coupon.save()

def get_default_coupon():
    coupon = Coupon.objects.get(code="DEFAULT_COUPON")
    return coupon.id

class UserCoupons(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.code
    
class Cart(models.Model):
    cart_id = models.CharField(max_length=50,blank=True)
    date_added = models.DateField(auto_now_add= True)
    user = models.ForeignKey(User, on_delete =models.CASCADE,default=None)
    total = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    coupon = models.ForeignKey(Coupon, on_delete =models.CASCADE,blank=True,default=get_default_coupon)


    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product,on_delete =models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price*self.quantity

    def __str__(self):
        return str(self.product)

class VariationsManger(models.Manager):
    def colors(self):
        return super(VariationsManger,self).filter(variation_category='color',is_active=True)
    
    def sizes(self):
        return super(VariationsManger,self).filter(variation_category='size',is_active=True)

Variation_category_choice=(
    ('color','color'),
    ('size','size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category =models.CharField(max_length=100, choices = Variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)
    objects = VariationsManger()

    def __unicode__(self):
        return self.product
    


class Payment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.payment_id

class Order(models.Model):
    STATUS =(
        ('Delivered','Delivered'),
        ('Placed','Placed'),
        ('Shipped','Shipped'),
        ('Cancelled','Cancelled'),
        ('Returned','Returned'),
        ('Return Pending','Return Pending'),
        ('Payment Pending','Payment Pending'), 
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(
               Coupon,
               on_delete=models.CASCADE, 
               default=get_default_coupon
                )
    order_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    order_note = models.TextField(blank=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    order_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, choices=[("Credit Card", "Credit Card"), ("Razorpay", "Razorpay"), ("Cash On Delivery", "Cash On Delivery")])
    is_completed = models.BooleanField(default=False)
    status = models.CharField(max_length=50,choices=STATUS,default='Placed')


    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered = models.BooleanField(default=False)

    def unit_price(self):
        return self.product.price*self.quantity

    def __str__(self):
        return str(self.product)
    
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
class ContactUs(models.Model):
    name = models.CharField(max_length=50,null=True, blank=True, default=None)
    email = models.EmailField(max_length=100,)
    mobile = models.CharField(max_length=50,null=True, blank=True, default=None)
    subject = models.CharField(max_length=50,null=True, blank=True, default=None)
    content = models.CharField(max_length=500,null=True, blank=True, default=None)

    def __str__(self):
        return self.email

class ReviewRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  
    subject = models.CharField(max_length=50,blank=True)
    review = models.TextField(max_length=500,blank=True)
    rating = models.FloatField(blank=True, null=True)
    review_reply = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject
    
class Wishlist(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    product=models.ForeignKey(Product, on_delete=models.CASCADE)

     

