import json
from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
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
import requests

# START : TAMBAHAN PROJECT PAS🔥

from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.utils.html import strip_tags
from django.core.paginator import Paginator

def product_list_json(request):
    # 1. Ambil parameter (?q=...&sort=...&page=...)
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '')
    page_number = request.GET.get('page', 1) # Default halaman 1

    # 2. Query Dasar
    products = Product.objects.select_related('store').all()

    # 3. Logika Search
    if q:
        products = products.filter(name__icontains=q)

    # 4. Logika Sort
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

    # 5. Logika Pagination (20 Produk per Halaman)
    paginator = Paginator(products, 20) 
    
    try:
        page_obj = paginator.page(page_number)
    except:
        # Jika halaman tidak valid (misal page=999), kembalikan halaman 1 atau terakhir
        page_obj = paginator.page(1)

    # 6. Serialisasi Data (Hanya data di halaman ini)
    data = []
    for product in page_obj.object_list:
        data.append({
            "pk": product.pk,
            "fields": {
                "name": product.name,
                "price": int(product.price),
                "rating": product.rating,
                "units_sold": product.units_sold,
                "image_url": product.image_url,
                "store": product.store.pk if product.store else None,
                "store_name": product.store.name if product.store else "Unknown Store",
            }
        })
    
    # 7. Return JSON dengan Metadata Pagination
    response_data = {
        'products': data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    }

    return JsonResponse(response_data, safe=False)

# 2. Endpoint untuk View Cart dalam JSON (Untuk Flutter)
def user_cart_json(request):
    # NOTE: allow guest/session-based cart (no authentication required)
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product').all()
    
    cart_data = []
    total_price = 0
    
    for item in items:
        item_total = item.product.price * item.quantity
        total_price += item_total
        cart_data.append({
            "id": item.pk, # ID CartItem
            "product": {
                "pk": item.product.pk,
                "name": item.product.name,
                "price": int(item.product.price),
                "image_url": item.product.image_url,
            },
            "quantity": item.quantity,
            "total_price": int(item_total)
        })

    return JsonResponse({
        "status": "success",
        "items": cart_data,
        "total_price": int(total_price)
    })


# 3. Endpoint Create Product khusus Flutter (CSRF Exempt & JSON Body)
@csrf_exempt
def create_product_flutter(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

    try:
        # IKUTI LOGIKA YANG SAMA DENGAN admin_session_required
        is_admin_session = request.session.get('is_admin', False)
        is_staff_user = bool(getattr(request.user, 'is_authenticated', False) and getattr(request.user, 'is_staff', False))

        if not (is_admin_session or is_staff_user):
            return JsonResponse({"status": "error", "message": "Hanya Admin yang boleh menambah produk"}, status=403)

        data = json.loads(request.body)

        # Cari instance FitnessSpot (Toko)
        store_id = data.get('store')
        store = None
        if store_id:
            store = FitnessSpot.objects.get(pk=store_id)

        new_product = Product.objects.create(
            name=data["name"],
            price=int(data["price"]),
            rating=data.get("rating", ""),  # Opsional
            units_sold=data.get("units_sold", ""),  # Opsional
            image_url=data["image_url"],
            store=store
        )

        return JsonResponse({"status": "success", "message": "Produk berhasil dibuat!"}, status=200)
    except FitnessSpot.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Toko tidak ditemukan"}, status=400)
    except KeyError as e:
        return JsonResponse({"status": "error", "message": f"Field wajib hilang: {e}"}, status=400)
    except ValueError as e:
        return JsonResponse({"status": "error", "message": f"Format nilai salah: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)


# API untuk mengambil daftar Fitness Spot (Toko) untuk Dropdown Flutter
def get_fitness_spots_json(request):
    spots = FitnessSpot.objects.all().order_by('name')
    data = []
    for spot in spots:
        data.append({
            "id": spot.pk,
            "name": spot.name
        })
    return JsonResponse(data, safe=False)

# END : TAMBAHAN PROJECT PAS🔥

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


@csrf_exempt
@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Ambil quantity dari request.POST atau JSON Body (Flutter biasa kirim JSON)
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except Exception:
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

    # Selalu return JSON untuk API Flutter
    cart.refresh_from_db() 
    return JsonResponse({
        'success': True,
        'message': f'"{product.name}" ditambahkan ke keranjang.',
        'cart_count': cart.items.count()
    })


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


@csrf_exempt
@require_POST
def remove_from_cart(request, pk):
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


@csrf_exempt
@require_POST
def update_cart(request, pk):
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
        if item and not removed:
             item_total = (item.product.price * item.quantity)

        return JsonResponse({
            'success': True,
            'message': message,
            'item_total_formatted': f"Rp{intcomma(int(item_total))}",
            'grand_total_formatted': f"Rp{intcomma(int(grand_total))}",
            'removed': removed
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def checkout(request):
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


@csrf_exempt
def edit_product_flutter(request, pk):
    if request.method != 'POST':
        return JsonResponse({
            "status": "error",
            "message": "Method not allowed"
        }, status=405)

    # 🔐 cek admin (sesuai sistemmu, BUKAN superuser)
    if not request.session.get('is_admin'):
        return JsonResponse({
            "status": "error",
            "message": "Hanya Admin yang boleh mengedit produk"
        }, status=403)

    try:
        product = Product.objects.get(pk=pk)
        data = json.loads(request.body)

        product.name = data.get('name', product.name)
        product.price = int(data.get('price', product.price))
        product.rating = data.get('rating', product.rating)
        product.units_sold = data.get('units_sold', product.units_sold)
        product.image_url = data.get('image_url', product.image_url)

        store_id = data.get('store')
        if store_id:
            product.store = FitnessSpot.objects.get(pk=store_id)

        product.save()

        return JsonResponse({
            "status": "success",
            "message": "Produk berhasil diperbarui"
        })

    except Product.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Produk tidak ditemukan"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
    

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
