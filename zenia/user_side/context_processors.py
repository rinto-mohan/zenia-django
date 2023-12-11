from user_side.models import *
from .forms import SignupForm,CustomLoginForm

def custom_context(request):
    
    products = Product.objects.all().filter(is_available=True)
    categories = Category.objects.all().filter(soft_deleted = False)
    sform = SignupForm()
    lform = CustomLoginForm() 
    cart = 0
    cart_items = 0
    quantity = 0
    wishlist = 0

    try:
        wishlist = Wishlist.objects.all().filter(user=request.user.id)
        cart = Cart.objects.get(user=request.user.id)
        if cart:
            try:
                cart_items = CartItem.objects.filter(cart=cart,is_active=True)
                quantity = sum(cart_item.quantity for cart_item in cart_items)
                
            except CartItem.DoesNotExist:
                pass
        
    except Cart.DoesNotExist:
        pass
    
    return {
        'products': products,
        'categories':categories,
        'lform':lform,
        'sform':sform,
        'cart_items':cart_items,
        'quantity':quantity,
        'wishlist':wishlist,
    }