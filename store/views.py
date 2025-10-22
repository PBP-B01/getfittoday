from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import F
from django.core.paginator import Paginator
from .models import Product, Cart, CartItem

# Helper untuk mendapatkan cart
def _get_or_create_cart(request):
    # Jika user login, gunakan cart milik dia
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(owner=request.user)
        return cart

    # Jika user belum login, gunakan session
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

# Daftar produk (dengan pencarian + sort)
def product_list(request):
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '')

    products = Product.objects.all()

    # Filter pencarian
    if q:
        products = products.filter(name__icontains=q)

    # Sorting produk
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'rating_desc':
        products = products.order_by('-rating')
    elif sort == 'rating_asc':
        products = products.order_by('rating')
    else:
        products = products.order_by('-created_at')

    # Pagination (20 produk per halaman)
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)

    context = {
        'products': products_page,
        'q': q,
        'sort': sort,
    }
    return render(request, 'product_list.html', context)


# Tambahkan produk ke cart
@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart = _get_or_create_cart(request)

    # Tambahkan atau update jumlah produk
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = F('quantity') + quantity
        item.save()
        item.refresh_from_db()
    else:
        item.quantity = quantity
        item.save()

    # Jika request via AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': cart.items.count()})

    return redirect('store:product_list')


# Lihat isi cart (ini pas checkout)
def view_cart(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    return render(request, 'checkout.html', {'cart': cart, 'items': items})

# Untuk checkout barang
def checkout(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'checkout.html', {
        'cart': cart,
        'items': items,
        'total': total,
    })
