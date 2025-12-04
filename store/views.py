import json
from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.db.models import F
from django.core.paginator import Paginator
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.template.loader import render_to_string
from decimal import Decimal, InvalidOperation 
from .models import Product, Cart, CartItem
from .forms import ProductForm
from home.models import FitnessSpot
from django.http import HttpResponse

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
    products_query = Product.objects.select_related('store').all()

    if q:
        products_query = products_query.filter(name__icontains=q)

    if sort == 'price_asc':
        products_query = products_query.order_by('price')
    elif sort == 'price_desc':
        products_query = products_query.order_by('-price')
    elif sort == 'rating_desc':
        products_query = products_query.order_by('-rating')
    elif sort == 'rating_asc':
        products_query = products_query.order_by('rating')
    else:
        products_query = products_query.order_by('-created_at')

    paginator = Paginator(products_query, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)

    context = {
        'products': products_page,
        'q': q,
        'sort': sort,
    }


    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('ajax') == '1':
        return render(request, 'product_list2.html', context)

    cart = _get_or_create_cart(request)
    context['cart_count'] = cart.items.count()
    context['fitness_spots'] = FitnessSpot.objects.all().order_by('name')

    return render(request, 'product_list.html', context)


@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart = _get_or_create_cart(request)
    
    item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product
    )

    if not created:
        item.quantity = F('quantity') + quantity
        item.save()
        item.refresh_from_db() 
    else:
        item.quantity = quantity
        item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart.refresh_from_db() 
        return JsonResponse({
            'success': True,
            'message': f'"{product.name}" ditambahkan ke keranjang.',
            'cart_count': cart.items.count()
        })

    return redirect('store:product_list')


def view_cart(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    total = 0
    for item in items:
        if hasattr(item, 'total_price') and callable(item.total_price):
             total += item.total_price()
        elif item.product and item.product.price is not None:
             total += (item.product.price * item.quantity)

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

    items = cart.items.select_related('product').all()
    total = 0
    for i in items:
        if hasattr(i, 'total_price') and callable(i.total_price):
            total += i.total_price()
        elif i.product and i.product.price is not None:
             total += (i.product.price * i.quantity)

    return JsonResponse({
        'success': True,
        'message': 'Item dihapus.',
        'cart_count': items.count(),
        'grand_total_formatted': f"Rp{intcomma(int(total))}"
    })


@require_POST
def update_cart(request, pk):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity'))
        cart = _get_or_create_cart(request)

        removed = False
        item = None
        message = ''
        
        if quantity < 1:
            item_qs = CartItem.objects.filter(cart=cart, product_id=pk)
            if item_qs.exists():
                item = item_qs.first()
                product_name = item.product.name
                item_qs.delete()
                removed = True
                message = f'"{product_name}" dihapus dari keranjang.'
            else:
                 return JsonResponse({'success': False, 'error': 'Item tidak ditemukan'}, status=404)
        else:
            item, created = CartItem.objects.update_or_create(
                 cart=cart, product_id=pk, defaults={'quantity': quantity}
            )
            item.refresh_from_db()
            message = f'Jumlah "{item.product.name}" diperbarui.'

        items = cart.items.select_related('product').all()
        grand_total = 0
        for i in items:
            if hasattr(i, 'total_price') and callable(i.total_price):
                grand_total += i.total_price()
            elif i.product and i.product.price is not None:
                 grand_total += (i.product.price * i.quantity)
        
        item_total = 0
        if item and hasattr(item, 'total_price') and callable(item.total_price) and not removed:
             item_total = item.total_price()
        elif item and item.product and item.product.price is not None and not removed:
             item_total = (item.product.price * item.quantity)


        return JsonResponse({
            'success': True,
            'message': message,
            'item_total_formatted': f"Rp{intcomma(int(item_total))}",
            'grand_total_formatted': f"Rp{intcomma(int(grand_total))}",
            'removed': removed
        })
    except CartItem.DoesNotExist:
         return JsonResponse({'success': False, 'error': 'Item tidak ditemukan'}, status=404)
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


def admin_session_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('is_admin', False):
            return view_func(request, *args, **kwargs)
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return JsonResponse({'success': False, 'error': 'Akses ditolak'}, status=403)
        else:
            login_url = reverse('central:login')
            return redirect(f'{login_url}?next={request.path}')
    return _wrapped_view


@require_POST
@admin_session_required
def create_product_ajax(request):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponseBadRequest("Hanya request AJAX yang diizinkan.")

    form = ProductForm(request.POST, request.FILES or None)
    if form.is_valid():
        try:
            product = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Produk "{product.name}" berhasil ditambahkan!',
                'product_id': product.pk
            })
        except Exception as e:
             return JsonResponse({'success': False, 'error': 'Terjadi kesalahan saat menyimpan produk.'}, status=500)
    else:
        errors_dict = {field: errors[0] for field, errors in form.errors.items()}
        return JsonResponse({
            'success': False,
            'errors': errors_dict
        }, status=400)


@admin_session_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    template_partial = 'edit_product2.html'
    template_full = 'edit_product.html'

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES or None, instance=product)
        if form.is_valid():
            try:
                form.save()
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Produk berhasil diperbarui!'
                    })
                else:
                    return redirect('store:product_list')
            except Exception as e:
                 if is_ajax:
                       return JsonResponse({'success': False, 'error': 'Gagal menyimpan pembaruan.'}, status=500)
                 else:
                       context = {'form': form, 'product': product, 'error_message': 'Gagal menyimpan pembaruan.'}
                       return render(request, template_full, context, status=500)
        else:
            context = {'form': form, 'product': product}
            if is_ajax:
                html_form = render_to_string(template_partial, context, request=request)
                return HttpResponseBadRequest(html_form, content_type='text/html')
            else:
                return render(request, template_full, context, status=400)
    else:
        form = ProductForm(instance=product)
        context = {
            'form': form,
            'product': product
        }
        if is_ajax:
            return render(request, template_partial, context)
        else:
            return render(request, template_full, context)


@require_POST
@admin_session_required
def delete_product(request, pk):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
         return JsonResponse({'success': False, 'error': 'Bad request'}, status=400)

    try:
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        return JsonResponse({
            'success': True,
            'message': f'Produk "{product_name}" berhasil dihapus.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Gagal menghapus produk.'}, status=500)
    

@require_GET
def view_product_detail(request, pk):
    if not (request.user.is_authenticated or request.session.get('is_admin', False)):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Anda harus login untuk melihat detail produk.'}, status=403)
        else:
            login_url = reverse('central:login')
            return redirect(f'{login_url}?next={request.path}')

    product = get_object_or_404(Product.objects.select_related('store'), pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    context = {'product': product}
    
    if is_ajax:
        return render(request, 'view_product_detail.html', context)
    else:
        return redirect('store:product_list')
    
def featured_products_api(request):
    try:
        products = Product.objects.order_by('-units_sold')[:15]
        
        data = []
        for product in products:
            data.append({
                'name': product.name,
                'price_formatted': f"Rp{intcomma(int(product.price))}",
                'image_url': product.image_url if product.image_url else 'https://via.placeholder.com/300x180.png?text=No+Image',
                'rating': product.rating or '-',
                'units_sold': product.units_sold or '',
                'view_url': reverse('store:product_list')
            })
        
        return JsonResponse({'products': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)