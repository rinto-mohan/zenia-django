from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from user_side.models import *
from django.contrib import messages,auth
from .forms import *
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
#activation
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator
from django.core.files import File
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect

import uuid
from django.utils import timezone
import razorpay
from django.conf import settings
from decimal import Decimal
import smtplib
from django.core.serializers.json import DjangoJSONEncoder
import base64
import uuid
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt





#for otp validation
import pyotp
import phonenumbers
from datetime import datetime, timedelta
from twilio.rest import Client
from phonenumbers import parse, PhoneNumberFormat
from django.urls import reverse
from PIL import Image

# for invoice download
from xhtml2pdf import pisa
from django.template.loader import get_template


# -------------------------------------------HELPER FUNCTIONS-----------------------------------------------



def previous_page(request):
    return redirect('/')

def contains_negative_digits(number):
    number_str = str(number)

    for char in number_str:
        if char == '-':
            return True  
        if char.isdigit() and int(char) < 0:
            return True  
    
    return False

def create_order_number():
    now = timezone.now()
    
    formatted_date_time = now.strftime('%Y%m%d%H%M%S')
    
    unique_identifier = str(uuid.uuid4().int)
    
    order_number = f'ZEN-{formatted_date_time}-{unique_identifier}'
    
    return order_number


#----------------------------------------- USER LOGIN AND LOGOUT--------------------------------------------------------------


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    # if request.user.is_authenticated and request.user.is_active and not request.user.is_admin:
    #     return redirect('/')
    
    products = Product.objects.all().filter(is_available=True)
    show_products = Product.objects.all().filter(is_available=True, starred = True)
    categories = Category.objects.all().filter(soft_deleted = False)
    try:
        cart = Cart.objects.get(user=request.user.id)
        if cart:
            cart_items = CartItem.objects.filter(cart=cart,is_active=True)
            quantity = sum(cart_item.quantity for cart_item in cart_items)
        else:
            messages.error(request,'Cart Does not exists')
    except Cart.DoesNotExist:
        cart = 0
        pass
    sform = SignupForm()
    lform = CustomLoginForm()
    if cart != 0:
        context = {
        'cart':cart,
        'products': products,
        'show_products': show_products,
        'categories':categories,
        'quantity':quantity,
        'cart_items':cart_items,
        'lform':lform,
        'sform':sform,
        }
    else:
        context = {
        'products': products,
         'show_products': show_products,
        'categories':categories,
        'lform':lform,
        'sform':sform,
        }
    
    return render(request,'user/index.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_sign_up(request):  
    if request.user.is_authenticated and request.user.is_active and not request.user.is_admin:
        return redirect('/')
    
    if request.method == 'POST':
        print(request.POST)
        sform = SignupForm(request.POST)
        
        if sform.is_valid():

            first_name = sform.cleaned_data['first_name']
            last_name = sform.cleaned_data['last_name']
            mobile = sform.cleaned_data['mobile']
            email = sform.cleaned_data['email']
            password = sform.cleaned_data['password']
            username = email.split("@")[0]

            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                mobile=mobile,
                password=password,
                )
            
            current_site = get_current_site(request)
            mail_subject = 'please activate your account'
            message =render_to_string('user/activate_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
           
            send_email =EmailMessage(mail_subject,message,to=[to_email])
            try:
                send_email.send()
            except Exception as e:
                messages.error(request, f"SMTP error: {e}")

            messages.success(request,'signup successfull, activation link is sent to the registerd email ')
            return redirect('user_login')
        
    else:
        sform = SignupForm() 
    
    context = {
        'sform': sform,
    }

    return render(request, 'user/user_signup.html', context)

@cache_control(no_cache=True,must_revalidate=True,no_store=True) 
def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        # user.referral_code = generate_referral_code()
        user.save()
        messages.success(request,'activation successfull')
        return redirect('user_login')
    else:
        messages.error(request,'invalid activation link')
        return redirect('user_sign_up')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_login(request):  
    if request.user.is_authenticated and request.user.is_active and not request.user.is_admin:
        return redirect('/')
      
    if request.method == 'POST':
        lform = CustomLoginForm(request.POST)
        if lform.is_valid(): 
            email = lform.cleaned_data.get('email')
            password = lform.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            print('user',user)
            if user is not None and not user.is_admin:
                if not user.is_blocked:
                    login(request, user)
                    request.session['user_name'] = user.id
                    messages.success(request, 'Login successful!')
                    cart_session = request.session.get('cart_session', {})
                    if cart_session:
                        user_cart, created = Cart.objects.get_or_create(user=request.user)
                        
                        for item_id, item_data in cart_session.items():
                            product = Product.objects.get(id=item_data['product_id'], soft_deleted=False)
                            
                            try:
                                cart_item1 = CartItem.objects.get(product=product, cart=user_cart)
                                cart_item1.quantity += int(item_data['quantity'])
                                cart_item1.save()
                            except CartItem.DoesNotExist:
                                cart_item1 = CartItem.objects.create(
                                    product=product,
                                    cart=user_cart,
                                    quantity=item_data['quantity'],
                                )

                            # if cart_item1:
                            #     cart_item1.quantity += item_data['quantity']
                            #     cart_item1.save()
                            # else:
                            #     cart_item = CartItem(
                            #         product=product,
                            #         cart=user_cart,
                            #         quantity=item_data['quantity'],
                            #     )
                                cart_item1.save()
                            
                        del request.session['cart_session']

                    return redirect(request.META.get('HTTP_REFERER', '/'))
                else:
                    messages.error(request, 'Your account is blocked, Contact administrator')
            else:
                messages.error(request, 'Account Does not exist in this mail')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        lform = CustomLoginForm()

    context = {
        'lform': lform,
    }

    return render(request, 'user/user_login.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
def user_logout(request):
    if 'user_name' in request.session:
        del request.session['user_name']
    logout(request)
    messages.success(request,'logout successfull')
    return redirect('user_login')

#----------------------------------------USER FORGOT PASSWORD-------------------------------------------------

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_forgot_password(request):
    if request.method=='POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user =User.objects.get(email__exact=email)

            current_site = get_current_site(request)
            expiration_time = timezone.now() + timedelta(minutes=1)
            expiration_time_str = expiration_time.isoformat()

            request.session['password_reset_token_expiration'] = expiration_time_str
            mail_subject = 'Reset your password'
            message = render_to_string('user/user_reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email =EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()

            messages.success(request,'Your password reset link send to registered email')
            return redirect('user_login')

        else:
            messages.error(request,'User does not exixts!!')
            return redirect('user_forgot_password')

    return render(request,'user/user-forgot-password.html')

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_reset_password_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
        
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        expiration_time_str = request.session.get('password_reset_token_expiration')
        if expiration_time_str:
            expiration_time = datetime.fromisoformat(expiration_time_str)
            if expiration_time > timezone.now():
                request.session['uid'] = uid
                messages.success(request, 'Reset your password')
                return redirect('user_reset_password')
            else:
                messages.error(request, 'Password reset link has expired.')
                return redirect('user_forgot_password')
        else:
            messages.error(request, 'Password reset link has expired.')
            return redirect('user_forgot_password')
    else:
        messages.error(request,'Try again!! link is Invalid ')
        return redirect('user_forgot_password')

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_reset_password(request):
    if request.method == 'POST':
        cform = ChangePasswordForm(request.POST)
        if cform.is_valid():
            password = cform.cleaned_data.get('password')
            confirm_password = cform.cleaned_data.get('confirm_password')

            if password == confirm_password:
                uid = request.session.get('uid')
                user = User.objects.get(pk=uid)
                user.set_password(password)
                user.save()
                request.session.flush()
                messages.success(request,'Reset password success')
                request.session.flush()
                return redirect('user_login')
            else:
                messages.error(request,'password doesnot match')
                return redirect('user_reset_password') 

    else:
        cform = ChangePasswordForm()
    
        context = {
            'cform': cform,
        }
        return render(request,'user/user_forgot_password.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            confirm_password = form.cleaned_data.get('confirm_password')
            try:
                email = request.session.get('user_email')
            except:
                messages.error(request, 'Request Timeout')
                return redirect('user_forgot_password')
            user = get_object_or_404(User, email=email)
            user.set_password(password)
            user.save()
            del request.session['user_email']
            messages.success(request, 'Password changed successfully, Login to your account')
            return redirect('user_login')
        else:
            messages.error(request, 'Invalid Form Submission')

    form = ChangePasswordForm()
    
    context = {
        'form': form,
    }

    return render(request, 'user/user_change_password.html',context)

def user_recover_password(request):

    return render(request, 'user/user_recover_password.html')


#----------------------------------------USER SHOP PAGE-------------------------------------------------


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_shop(request,category_id=None):

    if category_id != None:
        categories = get_object_or_404(Category, id=category_id)
        products = Product.objects.filter(category=categories,is_available=True)
        paginator = Paginator(products,8)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True)    
        paginator = Paginator(products,8)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    categories = Category.objects.all().filter(soft_deleted = False)

    context = {
        'products': paged_products,
        'product_count': product_count,
        'categories':categories,
        }
    return render(request,'user/user-shop.html',context)



#-----------------------------------------USER PRODUCT DETAILS-------------------------------------------


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_product_detail(request,id):
    product = Product.objects.get(id=id)
    context = {
        'product': product,
    }
    return render(request,'user/user-product-detail.html',context)

@require_POST
@csrf_exempt  # Use csrf_exempt for simplicity; you may want to add CSRF protection
def update_quantity(request, product_id, new_quantity):
    try:
        product = Product.objects.get(id=product_id)
        new_quantity = int(new_quantity)
        if new_quantity >= product.quantity:
            # return JsonResponse({'success': False, 'error': 'Product out of stock'})
            return JsonResponse({'success': True})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})


#----------------------------------------------USER CART--------------------------------------------------




def user_cart(request,total=0,quantity=0,cart_items=None):
    if request.user.is_authenticated and request.user.is_active and not request.user.is_admin:
        
        try:
            cart = Cart.objects.get(user=request.user)
            if cart:
                cart_items = CartItem.objects.filter(cart=cart,is_active=True)
                cart_itemss = CartItem.objects.filter(cart=cart)
                total = sum(cart_item.sub_total() for cart_item in cart_items)
                cart.total = total
                cart.grand_total = total
                print(cart.total)
                print(cart.grand_total)
                cart.save()
                quantity = sum(cart_item.quantity for cart_item in cart_items)
                for cart_item in cart_items:
                    cart_item.subtotal = cart_item.sub_total()
                    cart_item.save()
            else:
                messages.error(request,'Cart Does not exists')
        except Cart.DoesNotExist:
            cart_itemss = None
            total = 0
            quantity = 0
            cart = 0
        try:
            coupons = Coupon.objects.all().filter(is_active=True)
        except Coupon.DoesNotExist:
            pass

        try:
            pending_order = Order.objects.filter(status='Payment Pending',is_paid=False)
        except:
            pass

        context={
            'cart':cart,
            'quantity':quantity,
            'cart_items':cart_itemss,
            'coupons':coupons,
            'pending_order':pending_order,
        }
    else:
        cart_session = request.session.get('cart_session', {})
        cart_items = []

        for item_id, item_data in cart_session.items():
            product = Product.objects.get(id=item_data['product_id'], soft_deleted=False)
            cart_item = {
                'product': product,
                'quantity': item_data['quantity'],
                'subtotal': product.price * int(item_data['quantity']), 
            }
            cart_items.append(cart_item)

        total = sum(item['subtotal'] for item in cart_items)
        quantity = sum(int(item['quantity']) for item in cart_items)
        grand_total = total

        context = {

            'grand_total': grand_total,
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
        }

    return render(request,'user/user_cart.html',context)

def user_add_to_cart(request, id):
    if request.user.is_authenticated:
        if request.method == 'POST':

            quantity = request.POST['quantity']
            product = Product.objects.get(id=id,soft_deleted=False)  
            if product.quantity < int(quantity):
                messages.warning(request,'Sorry, Product is out of Stock')
                return redirect('user_add_to_cart',id)

            try:
                cart = Cart.objects.get(user=request.user)
            except:
                cart = Cart.objects.create(user=request.user)

            try:
                cart_item = CartItem.objects.get(product=product,cart=cart)
                if int(quantity) <= product.quantity :
                    cart_item.quantity += int(quantity)
                    
                else:
                    messages.error(request, 'Product stock out')
                    cart_item.quantity += 1
                    
                cart_item.save()
            except CartItem.DoesNotExist:
                cart_item=CartItem.objects.create(
                    product=product, 
                    quantity=0,
                    cart=cart,
                )
                if int(quantity) != 0:
                    cart_item.quantity += int(quantity)
                    

                cart_item.save()
            messages.success(request,'Item added to cart')
    else:
        if request.method == 'POST':

            quantity = request.POST['quantity']

            product = Product.objects.get(id=id, soft_deleted=False)

            cart_session = request.session.get('cart_session', {})
            cart_item = cart_session.get(str(product.id))
            if cart_item:
                if quantity:
                    cart_item['quantity'] += quantity
                else:
                    cart_item['quantity'] += 1
            else:
                cart_item = {
                    'product_id': product.id,
                    'quantity': 1,
                }
                if quantity:
                    cart_item['quantity'] = quantity
                else:
                    cart_item['quantity'] = 1

            cart_session[str(product.id)] = cart_item
            request.session['cart_session'] = cart_session
            
            messages.success(request, 'Item added to cart')

    return redirect(request.META.get('HTTP_REFERER', 'user_product_detail'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_remove_cart(request,id):
    if request.user.is_authenticated:
        cart= Cart.objects.get(user=request.user)
        product = get_object_or_404(Product,id=id)
        cart_item = CartItem.objects.get(product=product,cart=cart)
        if cart_item.quantity >1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    # else:
    #     cart_session = request.session.get('cart_session', {})
    #     product_id = id
    #     cart_item = cart_session.get(str(product_id))

    return redirect('user_cart')

def user_remove_cartitem(request,id):
    
    if request.user.is_authenticated:
        cart= Cart.objects.get(user=request.user)
        product = get_object_or_404(Product,id=id)
        cart_item = CartItem.objects.get(product=product,cart=cart)
        # product.quantity += int(cart_item.quantity)
        # product.save()
        cart_item.delete()
    else:
        cart_session = request.session.get('cart_session', {})
        product_id = id
        if str(product_id) in cart_session:
            del cart_session[str(product_id)]
            request.session['cart_session'] = cart_session

    return redirect('user_cart')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_quantity(request,id):
    product = get_object_or_404(Product, id=id, soft_deleted=False)
    if request.user.is_authenticated:
        cart= Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(product=product,cart=cart)
        if cart_item:
            cart_item.quantity +=1
            cart_item.save()
    else:
        cart_session = request.session.get('cart_session', {})
        cart_item = cart_session.get(str(product.id))

        if cart_item:
            cart_item['quantity'] += 1
            request.session['cart_session'] = cart_session

    return redirect(request.META.get('HTTP_REFERER', 'user_cart'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_quantity(request,id):
    product = get_object_or_404(Product, id=id, soft_deleted=False)
    if request.user.is_authenticated:
        cart= Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(product=product,cart=cart)
        if cart_item.quantity > 1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item = CartItem.objects.get(product=product,cart=cart)
            cart_item.delete()
    else:
        cart_session = request.session.get('cart_session', {})
        cart_item = cart_session.get(str(product.id))

        if cart_item and cart_item['quantity'] > 1:
            cart_item['quantity'] -= 1
            request.session['cart_session'] = cart_session
        elif cart_item and cart_item['quantity'] == 1:
            del cart_session[str(product.id)]
            request.session['cart_session'] = cart_session

    return redirect(request.META.get('HTTP_REFERER', 'user_cart'))

def update_cart_quantity(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_quantity = int(request.POST.get('quantity'))
        print('id:',product_id)
        print('count:',new_quantity)

        cart= Cart.objects.get(user=request.user) 
        cart_item = get_object_or_404(CartItem, product=product_id,cart=cart)
        cart_item.quantity = new_quantity
        cart_item.save()
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        grand_total = sum(cart_item.sub_total() for cart_item in cart_items)
        
        return JsonResponse({'message': 'Quantity updated successfully','grand_total':grand_total})

    return JsonResponse({'message': 'Invalid request method'}, status=400)

    
    # messages.error(request,'working')
    # if request.method == 'POST' and request.is_ajax():
    #     product_id = request.POST.get('product_id')
    #     cart= Cart.objects.get(user=request.user)
    #     cart_item = get_object_or_404(CartItem, product=product_id,cart=cart)

    #     if cart_item.quantity > 1:
    #         cart_item.quantity -= 1
    #         cart_item.save()

    #         response_data = {'new_quantity': cart_item.quantity}
    #         return JsonResponse(response_data)
    #     else:
    #         response_data = {'message': 'Minimum quantity reached'}
    #         return JsonResponse(response_data)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_add_save_later(request,cartitem_id):
    if request.user.is_authenticated:
        cartitem = get_object_or_404(CartItem, id=cartitem_id)
        if cartitem.is_active:
            cartitem.is_active = False
        else:
            cartitem.is_active = True
        cartitem.save()
    
    return redirect('user_cart')






def user_default_address(request,id):
    address = get_object_or_404(Address, id=id)
    if address.is_billing:
        address.is_billing=False        
    else:
        address.is_billing=True
    address.save()

    return redirect(request.META.get('HTTP_REFERER', 'user_checkout'))
    

#---------------------------------------USER PROFILE--------------------------------------------------


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
def user_profile(request):
    
    state_choices = Address.STATE_CHOICES
    addresses = Address.objects.filter(user_id=request.user.id)
    orders = Order.objects.filter(user=request.user)
    wallet = None
    if Wallet.objects.filter(user=request.user).exists():
        wallet = get_object_or_404(Wallet, user=request.user)

    if wallet is not None:
        context = {
            'state_choices': state_choices,
            'addresses': addresses,
            'orders':orders,
            'wallet':wallet,
            }
    else:
        context = {
            'state_choices': state_choices,
            'addresses': addresses,
            'orders':orders,
        }
    return render(request, 'user/user_profile.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
def user_profile_edit(request):
    if request.method =='POST':
        pform = ProfileEditForm(request.POST)
        if pform.is_valid():
            request.user.first_name = pform.cleaned_data['first_name']
            request.user.last_name = pform.cleaned_data['last_name']
            request.user.mobile = pform.cleaned_data['mobile']
            request.user.username = pform.cleaned_data['username']  

            request.user.profile_img = request.FILES.get('profile_img')

            request.user.save()
            messages.success(request, 'Profile Updated successfully')
            return redirect('user_profile')
        else:
            for field, errors in pform.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

    initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'username': request.user.username,
            'mobile': request.user.mobile,       
            'email': request.user.email,  
            'profile_img': request.user.profile_img, 
            }
    pform = ProfileEditForm(initial=initial_data)
    context={
        'pform':pform
    }
    return render(request, 'user/user_profile_edit.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_change_password_profile(request):
    if request.method == 'POST':
        form = ChangeCurrentPasswordForm(request.POST)
        form.user = request.user
        if form.is_valid():
            password = form.cleaned_data.get('password')
            
            request.user.set_password(password)
            request.user.save()
            
            messages.success(request, 'Password changed successfully, Login to your account')
            return redirect('user_profile')
        else:
            messages.error(request, 'Invalid Form Submission')

    form = ChangeCurrentPasswordForm()
    
    context = {
        'form': form,
    }

    return render(request, 'user/user_change_password_profile.html',context)


#---------------------------------------USER ADDRESS-----------------------------------------------------

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_add_address(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        address_1 = request.POST.get('address_1')
        address_2 = request.POST.get('address_2')
        state = request.POST.get('state')
        pin = request.POST.get('pin')
        mobile_number = request.POST.get('mobile_number')
        is_billing = request.POST.get('is_billing') 
        

        user = request.user
        if Address.objects.filter(user_id=request.user).exists():
            address = Address(
            user_id=user,
            name=name,
            city=city,
            address_1=address_1,
            address_2=address_2,
            state=state,
            pin=pin,
            mobile_number=mobile_number,
            )
            if is_billing is None:
                address.is_billing = False
            else:
                address.is_billing = True
        else:
            address = Address(
            user_id=user,
            name=name,
            city=city,
            address_1=address_1,
            address_2=address_2,
            state=state,
            pin=pin,
            mobile_number=mobile_number,
            )
            
            address.is_billing = True 

        invalid_characters = [' ', '*', '#','@','$','(','+','-','!','^','&']

        if any(char in name for char in invalid_characters):
            messages.error(request, 'Name cannot contain spaces or symbols.')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
        
        if len(name) < 3:
            messages.error(request,'Name is very short !')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))

        if address_1.isspace():
            messages.error(request,'Address cannot be empty')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))

        if city.isspace():
            messages.error(request,'City cannot be empty')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
        
        if len(pin) != 6 and not pin.isdigit() or contains_negative_digits(pin):
            messages.error(request,'Invalid Pincode ! Must be 6 digits')
            return redirect('user_profile')
        
        if len(mobile_number) != 10 and not mobile_number.isdigit():
            messages.error(request,'Mobile number must be 10 digits !')
            return redirect('user_profile')
        
        if contains_negative_digits(mobile_number):
            messages.error(request,'Invalid Mobile number !')
            return redirect('user_profile')
    
        address.save()
        messages.success(request,'Address added')
        return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
    

def user_edit_address(request,address_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        address_1 = request.POST.get('address_1')
        address_2 = request.POST.get('address_2')
        state = request.POST.get('state')
        pin = request.POST.get('pin')
        mobile_number = request.POST.get('mobile_number')
        is_billing = request.POST.get('is_billing') 

        print('address id :',address_id)
        save_address = Address.objects.get(id=address_id)
 
        save_address.name=name
        save_address.city=city
        save_address.address_1=address_1
        save_address.address_2=address_2
        if state:
            save_address.state=state
        save_address.pin=pin
        save_address.mobile_number=mobile_number
        if is_billing is None:
            save_address.is_billing = False
        else:
            save_address.is_billing = True

        invalid_characters = [' ', '*', '#','@','$','(','+','-','!','^','&']

        
        if any(char in name for char in invalid_characters):
            messages.error(request, 'Name cannot contain spaces or symbols.')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
        
        if len(name) < 3:
            messages.error(request,'Name is very short !')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))

        if address_1.isspace():
            messages.error(request,'Address cannot be empty')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))

        if city.isspace():
            messages.error(request,'City cannot be empty')
            return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
        
        if len(pin) != 6 and not pin.isdigit() or contains_negative_digits(pin):
            messages.error(request,'Invalid Pincode ! Must be 6 digits')
            return redirect('user_profile')
        
        if len(mobile_number) != 10 and not mobile_number.isdigit():
            messages.error(request,'Mobile number must be 10 digits !')
            return redirect('user_profile')
        
        if contains_negative_digits(mobile_number):
            messages.error(request,'Invalid Mobile number !')
            return redirect('user_profile')
        
        save_address.save()
        messages.success(request,'Address Updated')

        return redirect(request.META.get('HTTP_REFERER', 'user_profile'))
    
def user_delete_address(request,address_id):
    address = Address.objects.get(id=address_id)
    
    if address.is_billing:
        # Delete the current default address
        address.delete()

        user_addresses = Address.objects.filter(user_id=request.user)
        next_default_address = user_addresses.order_by('-id').exclude(id=address_id).first()

        if next_default_address:
            next_default_address.is_billing = True
            next_default_address.save()

    else:
        address.delete()


    return redirect(request.META.get('HTTP_REFERER', 'user_profile'))


# ------------------------------------------ORDERS-------------------------------------------------------

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_place_order(request):
    if request.method== 'POST':

        order_note  = request.POST.get('order_note')
        value  = request.POST.get('button_value')
        order_number = create_order_number()
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        if not cart_items:
            return redirect('user_shop')
        try:
            address = get_object_or_404(Address, user_id=request.user.id, is_billing=True)
        except:
            messages.error(request, 'Add an address to continue !')
            return redirect('user_checkout')
                
        order = Order(
            user=request.user,
            shipping_address=address,
            order_number=order_number,
            is_completed=False, 
            status='Payment Pending',
            is_paid = False,
            order_total = cart.grand_total,
            order_subtotal = cart.total,
        )

        if cart.coupon and cart.coupon != default_coupon:
                coupon = Coupon.objects.get(code=cart.coupon.code)
                order.coupon = coupon
                user_coupon = UserCoupons(
                    user=request.user,
                    coupon=coupon,
                    is_used=True,
                )
                user_coupon.save()
        if not order_note.isspace():
            order.order_note=order_note
        order.save()
        
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            cart_item.product.quantity -= cart_item.quantity
            cart_item.product.save()
            product = Product.objects.get(id=cart_item.product.id)
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                ordered=True,
                )
            order_item.unit_price=cart_item.subtotal
            order_item.save()

        if value == 'cod':
            payment = Payment(
                user=request.user,
                payment_id=order.order_number,
                payment_method="Cod",
                status="Not Paid",
                amount_paid=0,
            )
            payment.save()
            order.payment = payment
            order.payment_method = 'cod'
            order.status = 'Placed'
            order.save()

            order_items = OrderItem.objects.filter(order=order,ordered=True)
            today = datetime.now()
            context={
                    'order':order,
                    'order_items':order_items,
                    'cod':True,
                    'today':today,
                    }
            cart_items.delete()
            messages.success(request, 'YAY !! Your order is on its way')
            return render(request, 'user/user_order_confirm.html',context)
        
        elif value == 'wallet':
            payment = Payment(
                user=request.user,
                payment_id=order.order_number,
                payment_method="wallet",
                status="Paid",
                amount_paid=order.order_total,
            )
            payment.save()
            order.payment = payment
            order.payment_method = 'wallet'
            order.status = 'Placed'
            order.is_paid=True
            order.save()
            try:
                wallet = Wallet.objects.get(user=request.user)
                wallet.balance -= order.order_total
                wallet.save()
            except Wallet.DoesNotExist:
                pass

            order_items = OrderItem.objects.filter(order=order,ordered=True)
            today = datetime.now()
            context={
                    'order':order,
                    'order_items':order_items,
                    'wallet':True,
                    'today':today,
                    }
            cart_items.delete()
            messages.success(request, 'YAY !! Your order is on its way')
            return render(request, 'user/user_order_confirm.html',context)
            
        else:
            order.status = 'Placed'
            order.save()
            order_items = OrderItem.objects.filter(order=order)
            context={
            'order':order,
            'order_items':order_items,
                }
            cart_items.delete()
            return render(request, 'user/user_payment.html',context)
        
    return redirect('user_checkout')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_payment(request, id):
    order = get_object_or_404(Order, id=id)

    total_amount = order.order_total
    transaction_id = request.GET.get('transactionId')
    razorpay_client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
    payment = razorpay_client.payment.fetch(transaction_id)
    payment_status = payment['status']
    transaction_id = payment['id']

    payment = Payment(
        user=request.user,
        payment_id=transaction_id,
        payment_method="Razorpay",
        status="Paid",
        amount_paid=total_amount,
    )
    payment.save()

    order = get_object_or_404(Order, id=id)
    order.payment = payment
    order.is_paid = True
    order.status = 'Placed'
    order.save()

    messages.success(request, 'YAY !! Your order is on its way')

    order_items = OrderItem.objects.filter(order=order)
    today = datetime.now()

    context = {
        'order': order,
        'order_items': order_items,
        'payment': order.payment,
        'today': today,
    }

    return render(request, 'user/user_order_confirm.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_order_confirm(request,id):
    order = get_object_or_404(Order, id=id)
    order_items = OrderItem.objects.filter(order=order)

    context={
            'order':order,
            'order_items':order_items,
            'payment':order.payment,
            }
    return render(request, 'user/user_order_confirm.html',context)

def user_cancel_order(request):
    messages.error(request, 'Order Canceled')
    return redirect('user_cart')

def user_cancel_orderr(request,id):
    # id = int(order_id)
    try:
        order = get_object_or_404(Order, pk=id)
        order_items = OrderItem.objects.filter(order=order)
    except Order.DoesNotExist:
        pass

    if order.is_completed or order.status == 'Delivered':
        if (timezone.now() - order.order_date).days <= 10:
            order.status='Return Pending'
            messages.success(request,'Order return requested')
            order.save()
            return redirect('user_profile')
        else:
            messages.error(request,'You cannot return the product after 10 days')
            return redirect('user_profile')
    if order.is_paid:
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet.balance += order.order_total
            wallet.save()
        except:
            wallet = Wallet(
                user=request.user,
                balance=order.order_total,
            )
            wallet.save()
    try:
        for order_item in order_items:
            order_item.product.quantity += order_item.quantity
            order_item.product.save()
        order.status = 'Cancelled'
        order.save()
        messages.error(request, 'Order Canceled')
        return redirect('user_profile')
    except:
        pass
    return redirect('user_profile')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_order_details(request,id):
    order = get_object_or_404(Order, id=id)
    order_items = OrderItem.objects.filter(order=order)
    address = order.shipping_address
    context={
            'order':order,
            'order_items':order_items,
            'payment':order.payment,
            'address':address,
            }
    return render(request, 'user/user_order_details.html',context)


def generate_invoice_pdf(request, order_id):
    template = get_template('user/invoice_template.html')  # Replace with your actual template file
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    address = order.shipping_address

    context={
            'order':order,
            'order_items':order_items,
            'payment':order.payment,
            'address':address,
            }
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf'

    # Create a PDF object, and write the HTML content to it using pisa
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors with code %s <pre>%s</pre>' % (pisa_status.err, pisa_status.err_text))

    return response


# ----------------------------------------------COUPONS-----------------------------------------------------------


def user_coupon(request):
    return redirect('user_cart')

#--------------------------------------------USER CHECKOUT-------------------------------------------------


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
def user_checkout(request):

    cart = get_object_or_404(Cart, user=request.user.id)
    state_choices = Address.STATE_CHOICES
    addresses = Address.objects.filter(user_id=request.user.id)
    cart_items = CartItem.objects.filter(cart=cart,is_active=True)
    if cart_items:
        if request.method == 'POST':
            code = request.POST.get('coupon')
            grand_total = request.POST.get('grand_total')
            cart.total = grand_total
            cart.grand_total = grand_total
            cart.save()
            print('code',code)
            cart = get_object_or_404(Cart, user=request.user.id)
            for cartitem in cart_items:
                if cartitem.quantity > cartitem.product.quantity:
                    messages.error(request,'Product is Out of Stock !')
                    return redirect('user_cart')

            if code :
                try:
                    coupon = Coupon.objects.get(code=code)
                except ObjectDoesNotExist:
                    messages.error(request, 'Invalid Coupon Code')
                    return redirect('user_cart')
                
                if coupon.min_price > cart.total:
                    messages.error(request, f'Purchase for a minimum of {coupon.min_price} to avail this coupon')
                    return redirect('user_cart')
                
                if UserCoupons.objects.filter(coupon=coupon, user=request.user, is_used=True):
                    messages.error(request, 'This coupon has already used.')
                    return redirect('user_cart')
                
                if coupon.coupon_type == 'percentage':
                    print(cart.total)
                    print(cart.grand_total)
                    discount_percentage = Decimal(coupon.discount)
                    discount_price = (cart.total * discount_percentage / 100)
                    cart.grand_total = cart.total - discount_price
                    cart.save()
                    messages.success(request, f'Yayy you got {coupon.discount}% Off ')
                else:
                    cart.grand_total -= Decimal(coupon.discount)
                    cart.save()
                    messages.success(request, f'Yayy you got FLAT {coupon.discount} Off ')
                
                try:
                    wallet = Wallet.objects.get(user=request.user)
                except:
                    wallet = 0

                context = {
                        'state_choices': state_choices,
                        'addresses': addresses,
                        'cart':cart,
                        'coupon':coupon,
                        'cart_items':cart_items,
                        'discount_price':discount_price,
                        'wallet':wallet,
                        }
                
                request.session['applied_coupon_code'] = coupon.code
                request.session['applied_coupon_discount'] = float(coupon.discount)

                return render(request,'user/user_checkout.html',context)
            else:
                cart.grand_total=cart.total
                cart.save()
                messages.warning(request,'Coupon is not applied')

        try:
            wallet = Wallet.objects.get(user=request.user)
            
        except:
            wallet = 0

        context = {
            'state_choices': state_choices,
            'addresses': addresses,
            'cart':cart,
            'cart_items':cart_items,
            'wallet':wallet,
        }
        return render(request,'user/user_checkout.html',context)
    else:
        return redirect('user_cart')

   
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def search(request):
    keyword = request.GET.get('keyword') 
    products = Product.objects.none()

    if keyword:
        products = Product.objects.order_by('id').filter(product_name__icontains=keyword)
    else:
        return redirect('user_shop')

    context = {
        'products': products,
    }

    return render(request, 'user/user-shop.html', context)

def user_add_wishlist(request,id):
    product = get_object_or_404(Product, id=id)
    wishlist = Wishlist(
        product = product,
        user = request.user
    )
    wishlist.save()
    wishlist = Wishlist.objects.all().filter(user=request.user)
    return render(request, 'user/user_wishlist.html',{'wishlist':wishlist} )

def test_smtp_connection(request):
    # SMTP server settings
    host = 'smtp.gmail.com'
    port = 587  # Example port, change it to your SMTP server's port
    user = 'rintomona5@gmail.com'
    password = 'gqwl vlvv occv xrns'

    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        server.quit()
        return HttpResponse("SMTP connection successful")
    except Exception as e:
        return HttpResponse(f"SMTP connection failed: {e}")