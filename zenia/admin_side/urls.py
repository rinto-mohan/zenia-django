from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from admin_side import views
urlpatterns = [
    path('admin-index',views.admin_index,name='admin_index'),
    path('admin-login',views.admin_login,name='admin_login'),
    path('admin-logout',views.admin_logout,name='admin_logout'),
    path('admin_sales_report',views.admin_sales_report,name='admin_sales_report'),
    path('admin-products-list',views.admin_products_list,name='admin_products_list'),
    path('admin_coupons',views.admin_coupons,name='admin_coupons'),
    path('admin-add-product',views.admin_add_product,name='admin_add_product'),
    path('admin_edit_product/<int:product_id>',views.admin_edit_product,name='admin_edit_product'),
    path('admin_unlist_list_product/<int:product_id>',views.admin_unlist_list_product,name='admin_unlist_list_product'),
    path('admin_user_block_unblock/<int:id>',views.admin_user_block_unblock,name='admin_user_block_unblock'),
    path('admin_user_list/',views.admin_user_list,name='admin_user_list'),
    path('admin-reviews',views.admin_reviews,name='admin_reviews'),
    path('admin-categories',views.admin_categories,name='admin_categories'),
    path('admin-add-categories',views.admin_add_categories,name='admin_add_categories'),
    path('admin_enable_disable_category/<int:id>',views.admin_enable_disable_category,name='admin_enable_disable_category'),
    path('admin_edit_category/<int:id>',views.admin_edit_category,name='admin_edit_category'),
    path('admin-orders',views.admin_orders,name='admin_orders'),
    path('admin_delete_coupon/<int:id>/',views.admin_delete_coupon,name='admin_delete_coupon'),
    path('admin_order_details/<int:id>/',views.admin_order_details,name='admin_order_details'),
    path('admin_edit_order/<int:id>/',views.admin_edit_order,name='admin_edit_order'),
    path('admin_delete_order/<int:id>/',views.admin_delete_order,name='admin_delete_order'),
    path('admin_update_order_status/<int:order_id>/<str:new_status>/', views.admin_update_order_status, name='admin_update_order_status'),
    path('sales-report',views.sales_report,name='sales-report'),
    path('admin_update_coupon/<int:id>/',views.admin_update_coupon, name='admin_update_coupon'),



]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)