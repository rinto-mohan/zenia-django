from django.contrib import admin
from .models import  Category ,User ,Product
from django.contrib.auth.admin import UserAdmin


class AccountAdmin(UserAdmin):
    list_display = ('email','first_name','last_name','username','last_login','date_joined','is_active')
    list_display_links =('email','first_name','last_name')
    readonly_fields = ('last_login','date_joined')
    ordering = ('date_joined',)
    
    
    filter_horizontal =()
    list_filter=()
    fieldsets = ()
    
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields={'category_name':('category_name',)}
    list_display = ('category_name','description','is_available')

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields={'product_name':('product_name',)}
    list_display = ('product_name','price','category','brand','quantity','is_available')

admin.site.register(Category,CategoryAdmin)
admin.site.register(User,AccountAdmin)
admin.site.register(Product,ProductAdmin)