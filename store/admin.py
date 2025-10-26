from django.contrib import admin
from .models import Product, Cart, CartItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'store', 'rating', 'units_sold', 'created_at')
    list_filter = ('store', 'rating')
    search_fields = ('name', 'store__name')
    ordering = ('-created_at',)
    list_editable = ('price',)
    list_per_page = 25

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity')
    can_delete = False

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'session_key', 'created_at', 'updated_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('owner__username', 'session_key')
    inlines = [CartItemInline]
