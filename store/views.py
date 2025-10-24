import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import F
from django.core.paginator import Paginator
from django.contrib.humanize.templatetags.humanize import intcomma
from .models import Product, Cart, CartItem
from django.contrib.auth.decorators import user_passes_test
from .forms import ProductForm


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(owner=request.user)
        return cart
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def product_list(request):
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '')
    products = Product.objects.all()

    if q:
        products = products.filter(name__icontains=q)

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

    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)

    context = {
        'products': products_page,
        'q': q,
        'sort': sort,
    }
    

    if request.GET.get('ajax') == '1':
        return render(request, 'product_list2.html', context)

    cart = _get_or_create_cart(request)
    context['cart_count'] = cart.items.count()
    return render(request, 'product_list.html', context)

@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart = _get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        item.quantity = F('quantity') + quantity
    else:
        item.quantity = quantity
    item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'message': f'"{product.name}" ditambahkan ke keranjang.',
            'cart_count': cart.items.count()
        })

    return redirect('store:product_list')


def view_cart(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    total = sum(item.product.price * item.quantity for item in items)
    
    return render(request, 'checkout.html', {
        'cart': cart, 
        'items': items,
        'total': total
    })

@require_POST
def remove_from_cart(request, pk):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)
        
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, cart=cart, product_id=pk)
    item.delete()
    
    items = cart.items.all()
    total = sum(i.product.price * i.quantity for i in items)
    
    return JsonResponse({
        'success': True,
        'message': 'Item dihapus.',
        'cart_count': items.count(),
        'grand_total_formatted': f"Rp{intcomma(total)}"
    })

@require_POST
def update_cart(request, pk):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity'))
        cart = _get_or_create_cart(request)
        
        if quantity < 1:
            return remove_from_cart(request, pk)

        item = get_object_or_404(CartItem, cart=cart, product_id=pk)
        item.quantity = quantity
        item.save()
        
        items = cart.items.select_related('product').all()
        item_total = item.product.price * item.quantity
        grand_total = sum(i.product.price * i.quantity for i in items)

        return JsonResponse({
            'success': True,
            'item_total_formatted': f"Rp{intcomma(item_total)}",
            'grand_total_formatted': f"Rp{intcomma(grand_total)}"
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def checkout(request):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)

    try:
        cart = _get_or_create_cart(request)
        items = cart.items.all()
        if not items.exists():
             return JsonResponse({'success': False, 'error': 'Keranjang sudah kosong.'}, status=400)
        items.delete()

        return JsonResponse({'success': True, 'message': 'Checkout berhasil.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Produk berhasil diperbarui!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)

        return JsonResponse({
            'success': False,
            'message': 'Metode request tidak valid.'
        }, status=405)

    else:
        form = ProductForm(instance=product)
        return render(request, 'edit_product.html', {
            'form': form,
            'product': product
        })


@require_POST
@user_passes_test(is_admin)
def delete_product(request, pk):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)

    try:
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        return JsonResponse({'success': True, 'message': f'Produk "{product_name}" berhasil dihapus.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)