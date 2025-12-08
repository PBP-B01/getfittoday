from django.urls import path
from . import views
from store.views import proxy_image

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('product/create/', views.create_product_ajax, name='create_product_ajax'),
    path('product/<int:pk>/view/', views.view_product_detail, name='view_product_detail'),
    path('api/featured/', views.featured_products_api, name='featured_products_api'),
    # START : TAMBAHAN PROJECT PAS🔥
    # --- API KHUSUS FLUTTER ---
    path('api/products/', views.product_list_json, name='product_list_json'),
    path('api/cart/', views.user_cart_json, name='user_cart_json'),
    path('create-flutter/', views.create_product_flutter, name='create_product_flutter'),
    path('proxy-image/', proxy_image, name='proxy_image'),
    path('api/spots/', views.get_fitness_spots_json, name='get_fitness_spots_json'),
]