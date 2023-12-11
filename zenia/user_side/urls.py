from django.urls import path,include
from user_side import views
urlpatterns = [

    path('',views.index,name='index'),

    # Signup/login/Logout
    path('user_login/',views.user_login,name='user_login'),
    path('user_signup/',views.user_sign_up,name='user_signup'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('user_logout/',views.user_logout,name='user_logout'),

    # Forgot Password
    path('user_forgot_password/',views.user_forgot_password,name='user_forgot_password'),
    path('user_change_password_profile',views.user_change_password_profile,name='user_change_password_profile'),
    path('user_reset_password_validate/<uidb64>/<token>/',views.user_reset_password_validate,name='user_reset_password_validate'),
    path('user_reset_password/',views.user_reset_password,name='user_reset_password'),
    path('user_recover_password/',views.user_recover_password,name='user_recover_password'),

    # Shop
    path('user_shop/',views.user_shop,name='user_shop'),
    path('user_sort/<int:id>/',views.user_sort,name='user_sort'),
    path('user_shop/<int:category_id>/',views.user_shop,name='user_shop'),
    path('user_product_detail/<int:id>/',views.user_product_detail,name='user_product_detail'),
    

    # Profile
    path('user_profile',views.user_profile,name='user_profile'),
    path('user_profile_edit',views.user_profile_edit,name='user_profile_edit'),

    # Address
    path('user_add_address',views.user_add_address,name='user_add_address'),
    path('user_delete_address/<int:address_id>/',views.user_delete_address,name='user_delete_address'),
    path('user_edit_address/<int:address_id>/',views.user_edit_address,name='user_edit_address'),
    path('user_default_address/<int:id>/',views.user_default_address,name='user_default_address'),

    # Cart
    path('user_cart',views.user_cart,name='user_cart'),
    path('user_add_to_cart/<int:id>/',views.user_add_to_cart,name='user_add_to_cart'),
    path('user_remove_cartitem/<int:id>/',views.user_remove_cartitem,name='user_remove_cartitem'),
    path('update_cart_quantity/',views.update_cart_quantity,name='update_cart_quantity'),

    # Checkout
    path('user_checkout',views.user_checkout,name='user_checkout'),
    path('previous_page',views.previous_page,name='previous_page'),

    # Order
    path('user_place_order',views.user_place_order,name='user_place_order'),
    path('user_cancel_order',views.user_cancel_order,name='user_cancel_order'),
    path('user_cancel_orderrr/<int:id>/',views.user_cancel_orderr,name='user_cancel_orderrr'),
    path('user_order_confirm/<int:id>/',views.user_order_confirm,name='user_order_confirm'),
    path('user_order_details/<int:id>/',views.user_order_details,name='user_order_details'),

    # Payment
    path('user_payment/<int:id>/',views.user_payment,name='user_payment'),

    # Wishlist
    path('user_add_wishlist/<int:id>/',views.user_add_wishlist,name='user_add_wishlist'),
    path('user_wishlist/',views.user_wishlist,name='user_wishlist'),
    path('user_remove_wishlist/<int:id>/',views.user_remove_wishlist,name='user_remove_wishlist'),

    # Helper PATHS
    path('search/', views.search, name='search'),

]