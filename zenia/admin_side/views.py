from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import auth
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.contrib.auth.models import User
from user_side.models import *
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.http import Http404
from django.core.exceptions import ValidationError
from django.core.validators import validate_integer
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime,timedelta
from django.utils import timezone 
from django.http import JsonResponse
import json
from django.db.models import Sum,Count
from django.template.loader import get_template
from django.db.models.functions import TruncMonth
from django.db.models import F
from django.db.models import FloatField
from decimal import Decimal,InvalidOperation  




# Create your views here.
@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_index(request):
    if request.user.is_authenticated and request.user.is_admin and request.user.is_superadmin:
        # Calculate total revenue
        total_revenue = OrderItem.objects.filter(ordered=True).aggregate(total_revenue=Sum(F('product__price'), output_field=FloatField()))['total_revenue'] or 0.0

        # Total orders and total products
        total_orders = Order.objects.count()
        total_products = Product.objects.count()

        # Monthly report
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        monthly_report = OrderItem.objects.filter(
            ordered=True,
            order__order_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('order__order_date')
        ).values('month').annotate(
            total_revenue=Sum(F('product__price'), output_field=FloatField()),
            total_orders=Count('order')
        ).order_by('-month')

        # Last orders
        last_orders = Order.objects.order_by('-order_date')[:5]

        # Last month's data
        first_day_current_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_last_month = first_day_current_month - timedelta(days=first_day_current_month.day)
        last_month_data = monthly_report.filter(month=first_day_last_month)

        context = {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_products': total_products,
            'monthly_report': monthly_report,
            'last_orders': last_orders,
            'last_month_data': last_month_data,
            }

        messages.success(request, "Login Successful")
        return render(request, 'admin/index.html', context)

    return redirect('admin_login')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    if request.user.is_authenticated :
        if request.user.is_admin and request.user.is_superadmin:
            return redirect('admin_index')
    if request.method=="POST":
        admin_email=request.POST.get("email")
        admin_pass=request.POST.get("password")
        admin_user=auth.authenticate(email=admin_email,password=admin_pass)
        if admin_user is not None and admin_user.is_admin:
            auth.login(request,admin_user)
            request.session['admin_user'] = admin_user.id
            messages.success(request,"Login Successful")
            return redirect('admin_index')
        else:
            messages.warning(request,"Invalid Credentials!")
            return redirect('admin_login')

    return render(request,'admin/admin-login.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_logout(request):
    if 'admin_user' in request.session:
        del request.session['admin_user']
    auth.logout(request)
    messages.info(request,"Logout Successful")
    return render(request,'admin/admin-login.html')


@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_user_block_unblock(request,id):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            return redirect('admin_login')

    user = get_object_or_404(User, id=id)  
    try:
        if user.is_blocked:
            user.is_blocked=False
            user.is_active=True
            user.save()
            messages.success(request,'User is Unblocked')
        else:
            user.is_blocked = True
            user.is_active = False
            user.save()
            messages.success(request,'User is Blocked')
    except User.DoesNotExist:
        messages.warning(request, 'User does not exist')

    
    return redirect('admin_user_list')

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_user_list(request):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')

    users = User.objects.all().exclude(is_admin=True)
    context = {
        'users' : users
        }

    return render(request,'admin/admin-user-list.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_add_categories(request):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        description = request.POST.get('description')
        #is_available = request.POST.get('is_available')
        category_image = request.FILES.get('category_image')

        if category_name:
            if Category.objects.filter(category_name=category_name).exists():
                messages.warning(request,'Category name already exists')
                return redirect('admin_categories')
            elif ' ' in description:
                messages.warning(request,'Category description cannot be empty !')
                return redirect('admin_categories')
            else:
                category = Category(
                    category_name=category_name,
                    description=description,
                )
                if category_image:
                    category.category_image = category_image
                category.save()
                messages.success(request,'Category added successfully')

    return redirect('admin_categories')

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_enable_disable_category(request,id):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')
    
    
    category = get_object_or_404(Category, id=id)
    try:
        if category.soft_deleted:
            category.soft_deleted = False
            category.save()
            Product.objects.filter(category=category).update(soft_deleted=False)
            messages.success(request,'Category Enabled')
            return redirect('admin_categories')
        else:
            category.soft_deleted = True
            category.save()
            Product.objects.filter(category=category).update(soft_deleted=True)
            messages.success(request,'Category Disabled')
            return redirect('admin_categories')
    except :
            messages.warning(request,'Oops ! Error occurred')
    
    return redirect('admin_categories')

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_edit_category(request,id):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')
    
    try:
        category = get_object_or_404(Category, id=id)
    except Http404:
        raise Http404("category does not exist")

    if request.method == 'POST':
        category_name = request.POST['category_name']
        description = request.POST['description']
        category_image = request.FILES.get('category_image')
        
        if category_name:
            if Category.objects.filter(category_name=category_name).exists():
                messages.warning(request,'Category name already exists')
                return redirect('admin_categories')
            elif ' ' in description:
                messages.warning(request,'Category description cannot be empty !')
                return redirect('admin_categories')
            else:
                category.category_image = category_image
                category.category_name = category_name
                category.description = description
                try:
                    category.save()
                    messages.success(request, 'category updated successfully!')
                    return redirect('admin_categories')
                except:
                    messages.warning(request, 'Oops! Error occurred while updating the Category.')

    context = {
        'category' : category
        }
    
    return render(request, 'admin/admin-edit-category.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_categories(request):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')

    categories = Category.objects.all()
    context = {
        'categories' : categories
        }

    return render(request,'admin/admin-categories.html',context)  
    
      

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_products_list(request):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')

    products = Product.objects.all()
    context={
        'products' : products
        }

    return render(request,'admin/admin-products-list.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_add_product(request):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')

    if request.method == 'POST':

        product_name = request.POST['product_name']
        category_id = request.POST['category']
        brand = request.POST['brand']
        description = request.POST['description']
        price = request.POST['price']
        offer_price = request.POST['offerprice']
        quantity = request.POST['quantity']
        star = request.POST.get('star')
        product_images = request.FILES.get('product_images')
        product_images_1 = request.FILES.get('product_images_1')
        product_images_2 = request.FILES.get('product_images_2')
        product_images_3 = request.FILES.get('product_images_3')

        if star == '1':
            product.star = True
        
        if product_images:
            if not product_images.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        else:
            messages.error(request, 'Oops! First and Second image is Required.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))

        if product_images_1:
            if not product_images_1.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))                
        else:
            messages.error(request, 'Oops! First and Second image is Required.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))

        if product_images_2:
            if not product_images_2.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))


        if product_images_3:
            if not product_images_3.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))

        if product_name.isspace():
            messages.error(request, 'Oops! Product name cannot be empty.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        
        if category_id.isspace():
            messages.error(request, 'Oops! Category cannot be empty.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        
        if brand.isspace():
            messages.error(request, 'Oops! Brand cannot be empty.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        
        decimal_price = Decimal(price)
        if price.isspace() or decimal_price <= 0.0:
            messages.error(request, 'Price should be a valid number.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        
        decimal_offer_price = Decimal(offer_price) 
        if offer_price.isspace() or decimal_offer_price <= 0.0:
            messages.error(request, 'Offer Price should be a valid number.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
        
        if offer_price >= price:
            messages.error(request, 'Offer Price cannot be more than Original Price')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))

        if not quantity.isdigit() or int(quantity) <= 0:
            messages.error(request, 'Quantity should be a valid number.')
            return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))       
        
        category = Category.objects.get(id=category_id)
        product = Product(
                product_name=product_name,
                category_id=category,
                brand=brand,
                description=description,
                price=decimal_price,
                quantity=quantity,
                offer_price=decimal_offer_price,
                product_images = product_images,
                product_images_1 = product_images_1,
                product_images_2 = product_images_2,
                product_images_3 = product_images_3,
            )

        product.save()
        messages.success(request, 'Product added successfully!')
        return redirect('admin_products_list')
        
    categories = Category.objects.all().filter(soft_deleted=False)
    context={
        'categories':categories
        }
    
    return render(request,'admin/admin-add-product.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_edit_product(request, product_id):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')
    
    try:
        product = get_object_or_404(Product, id=product_id)
    except Http404:
        raise Http404("Product does not exist")

    if request.method == 'POST':
        product_name = request.POST['product_name']
        category_id = request.POST['category']
        brand = request.POST['brand']
        description = request.POST['description']
        price = request.POST.get('price')
        offer_price = request.POST['offerprice']
        quantity = request.POST['quantity']
        star = request.POST.get('star')
        product_images = request.FILES.get('product_images')
        product_images_1 = request.FILES.get('product_images_1')
        product_images_2 = request.FILES.get('product_images_2')
        product_images_3 = request.FILES.get('product_images_3')

        

        if star == '1':
            product.star = True
        
        if product_images:
            if not product_images.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            else:
                product.product_images = product_images
        
        if product_images_1:
            if not product_images_1.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            else:
                product.product_images_1 = product_images_1

        if product_images_2:
            if not product_images_2.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            else:
                product.product_images_2 = product_images_2

        if product_images_3:
            if not product_images_3.content_type.startswith('image'):
                messages.error(request, 'Oops! Only images allowed.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            else:
                product.product_images_3 = product_images_3
        
        product = get_object_or_404(Product, id=product_id)

        if product_name:
            if product_name.isspace():
                messages.error(request, 'Oops! Product name cannot be empty.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            product.product_name = product_name
        if category_id:
            if category_id.isspace():
                messages.error(request, 'Oops! Category cannot be empty.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            category = Category.objects.get(id=category_id)
            product.category = category
        if brand:
            if brand.isspace():
                messages.error(request, 'Oops! Brand cannot be empty.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            product.brand = brand
        if description:
            product.description = description
        if quantity:
            if not quantity.isdigit() or int(quantity) <= 0:
                messages.error(request, 'Quantity should be a valid number.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))  
            product.quantity = int(quantity)

        if price:
            decimal_price = Decimal(price)
            if price.isspace() or decimal_price <= 0.0:
                messages.error(request, 'Price should be a valid number.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))
            product.price = decimal_price

        if offer_price:
            decimal_offer_price = Decimal(offer_price) 

            if offer_price.isspace() or decimal_offer_price <= 0.0:
                messages.error(request, 'Offerprice should be a valid number.')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))  
            product.offer_price = decimal_offer_price

            if offer_price >= price:
                messages.error(request, 'Offer Price cannot be more than Original Price')
                return redirect(request.META.get('HTTP_REFERER', 'admin_products_list'))        


        try:
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products_list')
        except ValidationError as e:
            messages.error(request, f'Validation error: {", ".join(e)}')
        except IntegrityError:
            messages.error(request, 'Oops! Error occurred while updating the product.')

    categories = Category.objects.all()
    context = {
        'categories': categories,
        'product': product,
        }

    return render(request, 'admin/admin-edit-product.html', context)


@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_unlist_list_product(request,product_id):
    if not request.user.is_authenticated :
        if not request.user.is_admin and request.user.is_superadmin:
            messages.success(request,"Please Login")
            return redirect('admin_login')
    product = get_object_or_404(Product, id=product_id)
    try:
        if product.soft_deleted:
            product.soft_deleted = False
            product.save()
            messages.success(request,'Product Listed')
            return redirect('admin_products_list')
        else:
            product.soft_deleted = True
            product.save()
            messages.success(request,'Product Unlisted')
            return redirect('admin_products_list')
    except:
        messages.error(request,'Error Occurred while updating')
        return redirect('admin_products_list')

def admin_coupons(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        discount = request.POST.get('discount')
        expiry_date = request.POST.get('expiry_date')
        min_price = request.POST.get('min_price')
        max_uses = request.POST.get('max_uses')
        description = request.POST.get('description')
        coupon_type = request.POST.get('discount_type')
        
        if code:
            if Coupon.objects.all().filter(code=code).exists():
                messages.warning(request, 'Coupon code already exists')
                return redirect('admin_coupons')
        
        if code.isspace():
            messages.warning(request, 'Coupon code cannot be empty')
            return redirect('admin_coupons')
        
        if discount.isspace() or float(discount) <= 0:
            messages.warning(request, 'Coupon discount cannot be empty or invalid')
            return redirect('admin_coupons')
        
        try:
            expiry_date = datetime.strptime(expiry_date, '%d/%m/%Y')  # Indian date format
        except ValueError:
            messages.warning(request, 'Invalid expiration date format')
            return redirect('admin_coupons')
        current_date = date.today()
        
        if expiry_date:
            current_date = datetime.combine(current_date, datetime.min.time())
            if expiry_date < current_date:
                messages.warning(request, 'Enter valid Expiry date')
                return redirect('admin_coupons')
        
        if max_uses.isspace() or float(max_uses) <= 0:
            messages.warning(request, 'Enter atleast 1 max use')
            return redirect('admin_coupons')
        
        if min_price.isspace() or float(min_price) <= 0 :
            messages.warning(request, 'Minimum price cannot be 0')
            return redirect('admin_coupons')

        coupon = Coupon(
             code=code,
             discount=discount,
             expiration_date=expiry_date,
             min_price=min_price,
             max_uses=max_uses,
             description=description,
            )
        coupon.coupon_type=coupon_type
        coupon.save()
        messages.success(request, 'Added new Coupon')
        return redirect('admin_coupons')

    coupons = Coupon.objects.all().filter(is_active=True).exclude(code="DEFAULT_COUPON")
    COUPON_CHOICES = Coupon.COUPON_CHOICES

    context={
        'coupons':coupons,
        'COUPON_CHOICES':COUPON_CHOICES,
        }

    return render(request,'admin/admin_coupons.html',context)

@login_required(login_url='admin_login')
def admin_update_coupon(request,id):
    coupon = get_object_or_404(Coupon, id = id)
    COUPON_CHOICES = Coupon.COUPON_CHOICES
    context={
        'coupon':coupon,
        'COUPON_CHOICES':COUPON_CHOICES,
        }
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        discount = request.POST.get('discount')
        expiry_date = request.POST.get('expiry_date')
        min_price = request.POST.get('min_price')
        max_uses = request.POST.get('max_uses')
        description = request.POST.get('description')
        coupon_type = request.POST.get('discount_type')

        print('id',id)
    
        coupon = get_object_or_404(Coupon, id = id)

        if code:
            if Coupon.objects.filter(code=code).exclude(id=id).exists():
                messages.warning(request, 'Coupon code already exists')
                return render(request,'admin/admin_edit_coupon.html',context)
            if code.isspace():
                messages.warning(request, 'Coupon code cannot be empty')
                return render(request,'admin/admin_edit_coupon.html',context)
            coupon.code = code
        if discount:
            if discount.isspace() or float(discount) <= 0:
                messages.warning(request, 'Coupon discount cannot be empty or invalid')
                return render(request,'admin/admin_edit_coupon.html',context)
            coupon.discount = discount
        try:
            expiry_date = datetime.strptime(expiry_date, '%d/%m/%Y')  # Indian date format
        except ValueError:
            messages.warning(request, 'Invalid expiration date format')
            return render(request,'admin/admin_edit_coupon.html',context)
        current_date = date.today()
        if expiry_date:
            current_date = datetime.combine(current_date, datetime.min.time())
            if expiry_date < current_date:
                messages.warning(request, 'Enter valid Expiry date')
                return render(request,'admin/admin_edit_coupon.html',context)
            coupon.expiration_date = expiry_date
        if min_price:
            if min_price.isspace() or float(min_price) <= 0 :
                messages.warning(request, 'Minimum price cannot be 0')
                return render(request,'admin/admin_edit_coupon.html',context)
            coupon.min_price = min_price
        if max_uses:
            if max_uses.isspace() or float(max_uses) <= 0:
                messages.warning(request, 'Enter atleast 1 max use')
                return render(request,'admin/admin_edit_coupon.html',context)
            coupon.max_uses = max_uses
        if description:
            coupon.description = description
        if coupon_type:
            coupon.coupon_type = coupon_type
        coupon.save()
        messages.success(request, 'Updated Coupon')
        return redirect('admin_coupons')

    return render(request,'admin/admin_edit_coupon.html',context)

@login_required(login_url='admin_login')
def admin_delete_coupon(request,id):

    coupon = get_object_or_404(Coupon, id = id)
    coupon.delete()
    return redirect('admin_coupons')

@login_required(login_url='admin_login')
def admin_delete_order(request,id):
    return render(request,'admin/admin-orders-detail.html')

@login_required(login_url='admin_login')
def admin_edit_order(request,id):
    return render(request,'admin/admin-orders-detail.html')

@login_required(login_url='admin_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_review(request):
    reviews = ReviewRating.objects.all()
    paginator = Paginator(reviews,6)
    page = request.GET.get('page')
    paged_reviews = paginator.get_page(page)
    reviews_count = reviews.count()
    context={
        'reviews':reviews,
        'reviews':paged_reviews,
        'reviews_count':reviews_count,
        }

    return render(request, 'admin/admin_review.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_review_replay(request, id):
    review = get_object_or_404(ReviewRating, id=id)

    if request.method == 'POST':
        review_reply = request.POST.get('review_reply')
        review.review_reply = review_reply
        review.save() 
        return redirect('admin_review')

    context = {
        'review': review, 
        }
    return render(request, 'admin/admin_review_replay.html', context)

@login_required(login_url='admin_login')
def get_weekly_sales(request):
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=7)

    return OrderItem.objects.filter(
        order__order_date__range=(start_date, end_date)
    ).values('product__product_name').annotate(weekly_sales=Sum('quantity'))


@login_required(login_url='admin_login')
def get_monthly_sales(request):
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=30)

    return OrderItem.objects.filter(
        order__order_date__range=(start_date, end_date)
    ).values('product__product_name').annotate(monthly_sales=Sum('quantity'))


@login_required(login_url='admin_login')
def get_yearly_sales(request):
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=365)

    return OrderItem.objects.filter(
        order__order_date__range=(start_date, end_date)
    ).values('product__product_name').annotate(yearly_sales=Sum('quantity'))


@login_required(login_url='admin_login')
def sales_report(request):
    weekly_sales_data = list(get_weekly_sales(request).values('product__product_name','weekly_sales'))  # Convert QuerySet to a list of dictionaries
    monthly_sales_data = list(get_monthly_sales(request).values('product__product_name','monthly_sales'))
    yearly_sales_data = list(get_yearly_sales(request).values('product__product_name','yearly_sales'))
    sales_data = {
        'weekly_sales': weekly_sales_data,
        'monthly_sales': monthly_sales_data,
        'yearly_sales': yearly_sales_data,
        }
    print('sales',sales_data)
    return JsonResponse(sales_data, safe=False)

@login_required(login_url='admin_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_contact(request):
    contact_us = ContactUs.objects.all()
  
    context = {
        'contact_us': contact_us, 
        }
    return render(request, 'admin/admin_contact.html', context)

@login_required(login_url='admin_login')
def admin_panel(request):     
    return render(request,'admin/admin-login.html')

@login_required(login_url='admin_login')
def admin_brands(request):     
    return render(request,'admin/admin-brands.html')

@login_required(login_url='admin_login')
def admin_account_register(request):
    return render(request,'admin/admin-account-register.html')

@login_required(login_url='admin_login')
def admin_user_card(request):
    return render(request,'admin/admin-user-cards.html')

@login_required(login_url='admin_login')
def admin_account_login(request):
    return render(request,'admin/admin-account-login.html')

@login_required(login_url='admin_login')
def admin_settings(request):
    return render(request,'admin/admin-settings.html')

@login_required(login_url='admin_login')
def admin_blank(request):
    return render(request,'admin/admin-blank.html')

@login_required(login_url='admin_login')
def admin_reviews(request):
    return render(request,'admin/admin-reviews.html')

@login_required(login_url='admin_login')
def admin_error_404(request):
    return render(request,'admin/admin-error-404.html')

@login_required(login_url='admin_login')
def admin_form_product(request):
    return render(request,'admin/admin-form-product.html')

@login_required(login_url='admin_login')
def admin_orders(request):
      
    orders = Order.objects.all()
    paginator = Paginator(orders,10)
    page = request.GET.get('page')
    paged_orders = paginator.get_page(page)
    orders_count = orders.count()
    users = User.objects.filter(is_blocked=False, is_active=True, is_admin=False)

    context={
        'orders':orders,
        'orders':paged_orders,
        'orders_count':orders_count,
        'users':users,
        }
    return render(request,'admin/admin-orders.html',context)

@login_required(login_url='admin_login')
def admin_order_details(request,id):
    order = Order.objects.get(id=id)
    order_products = OrderItem.objects.filter(order=order)
    
    payments = order.payment

    context = {
        'order_products': order_products,
        'order': order,
        'payments': payments,
        }
    return render(request,'admin/admin-orders-detail.html',context)

@login_required(login_url='admin_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_update_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, pk=order_id)
    order_products = OrderItem.objects.filter(order=order)
    
    if new_status == 'Cancelled':
        order.status = 'Cancelled'
        for order_product in order_products:
            product = order_product.product
            product.quantity += order_product.quantity
            product.save()
        if order.payment.payment_method == 'Razorpay':
            try:
                user_wallet = Wallet.objects.get(user=order.user)
                user_wallet.balance += Decimal(order.order_total)
                user_wallet.save()
            except ObjectDoesNotExist:
                user_wallet = Wallet.objects.create(user=order.user, balance=Decimal(order.order_total))
                user_wallet.save()

    elif new_status == 'Accepted':
        order.status = 'Shipped'
    elif new_status == 'Delivered':
        order.status = 'Delivered'
        order.is_paid=True
    elif new_status == 'Return':
        order.status = 'Returned'
            
    if new_status == 'Return':
        for order_product in order_products:
            product = order_product.product
            product.quantity += order_product.quantity
            product.save()
            try:
                user_wallet = Wallet.objects.get(user=order.user)
                user_wallet.balance += Decimal(order.order_total)
                user_wallet.save()
            except ObjectDoesNotExist:
                user_wallet = Wallet.objects.create(user=order.user, balance=Decimal(order.order_total))
                user_wallet.save()
    
    order.save()
    messages.success(request, f"Order #{order.order_number} has been updated to '{new_status}' status.")
    
    return redirect('admin_orders')

@login_required(login_url='admin_login')
def admin_sales_report(request):
    orders = Order.objects.all()
    paginator = Paginator(orders,10)
    page = request.GET.get('page')
    paged_orders = paginator.get_page(page)
    orders_count = orders.count()
    users = User.objects.filter(is_blocked=False, is_active=True, is_admin=False)

    context={
        'orders':orders,
        'orders':paged_orders,
        'orders_count':orders_count,
        'users':users,
        }

    return render(request,'admin/admin_sales_report.html',context)