import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from django.db import IntegrityError
from .models import Product, Cart, CartItem
from home.models import FitnessSpot
from .forms import ProductForm

User = get_user_model()

class StoreModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.spot = FitnessSpot.objects.create(
            pk='testSpotPK',
            name='Test Fitness Spot',
            address='123 Test St',
            latitude='-6.5000',
            longitude='106.8000'
        )
        cls.product1 = Product.objects.create(
            name='Test Product 1',
            price=Decimal('50000'),
            store=cls.spot,
            rating='4.5',
            units_sold='100 terjual',
            image_url='http://example.com/img1.jpg'
        )
        cls.product2 = Product.objects.create(
            name='Test Product 2',
            price=Decimal('75000'),
            store=cls.spot,
            image_url='http://example.com/img2.jpg'
        )

    def test_product_creation_and_str(self):
        self.assertEqual(self.product1.name, 'Test Product 1')
        self.assertEqual(self.product1.price, Decimal('50000'))
        self.assertEqual(self.product1.store, self.spot)
        self.assertEqual(str(self.product1), 'Test Product 1 — Rp50,000')

    def test_cart_creation_authenticated_user(self):
        cart = Cart.objects.create(owner=self.user)
        self.assertEqual(cart.owner, self.user)
        self.assertEqual(cart.session_key, '')
        self.assertEqual(str(cart), f'Cart({self.user.username})')

    def test_cart_creation_anonymous_user(self):
        session_key = 'testsessionkey123'
        cart = Cart.objects.create(session_key=session_key)
        self.assertIsNone(cart.owner)
        self.assertEqual(cart.session_key, session_key)
        self.assertEqual(str(cart), f'Cart(session={session_key})')

    def test_cartitem_creation_and_total_price(self):
        cart = Cart.objects.create(owner=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=3)
        self.assertEqual(item.cart, cart)
        self.assertEqual(item.product, self.product1)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(str(item), f'{self.product1.name} x3')
        expected_item_total = Decimal('50000') * 3
        self.assertEqual(item.total_price(), expected_item_total)

    def test_cart_total_price(self):
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        expected_cart_total = (Decimal('50000') * 2) + (Decimal('75000') * 1)
        self.assertEqual(cart.total_price(), expected_cart_total)

    def test_cart_total_price_empty(self):
        cart = Cart.objects.create(owner=self.user)
        self.assertEqual(cart.total_price(), Decimal('0'))

    def test_cartitem_unique_together(self):
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(cart=cart, product=self.product1, quantity=1)


class ProductFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.spot = FitnessSpot.objects.create(
            pk='formTestSpotPK',
            name='Form Test Spot',
            address='456 Form Ave',
            latitude='-6.5100',
            longitude='106.8100'
        )
        cls.valid_data = {
            'name': 'Valid Product',
            'price': 100000,
            'rating': '4.8',
            'units_sold': '50+',
            'image_url': 'http://example.com/valid.jpg',
            'store': cls.spot.pk
        }

    def test_valid_product_form(self):
        form = ProductForm(data=self.valid_data)
        if not form.is_valid():
            print("Form Errors:", form.errors.as_json())
        self.assertTrue(form.is_valid())

    def test_product_form_save(self):
        form = ProductForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        product = form.save()
        self.assertEqual(product.name, 'Valid Product')
        self.assertEqual(product.price, Decimal('100000'))
        self.assertEqual(float(product.rating) if product.rating else None, 4.8)
        self.assertEqual(product.store, self.spot)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_product_form_missing_required_fields(self):
        invalid_data = self.valid_data.copy()
        del invalid_data['name']
        del invalid_data['price']
        del invalid_data['image_url']
        del invalid_data['store']
        form = ProductForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('price', form.errors)
        self.assertIn('image_url', form.errors)
        self.assertIn('store', form.errors)

    def test_product_form_invalid_price_negative(self):
        invalid_data = self.valid_data.copy()
        invalid_data['price'] = -10000
        form = ProductForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
        self.assertEqual(form.errors['price'], ['Harga tidak boleh negatif.'])

    def test_product_form_invalid_rating_too_high(self):
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = '5.1'
        form = ProductForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['Rating harus antara 0.0 dan 5.0.'])

    def test_product_form_invalid_rating_too_low(self):
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = '-0.1'
        form = ProductForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['Rating harus antara 0.0 dan 5.0.'])

    def test_product_form_invalid_rating_non_numeric(self):
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = 'abc'
        form = ProductForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['Masukkan nilai rating numerik yang valid.'])

    def test_product_form_rating_optional(self):
        data = self.valid_data.copy()
        del data['rating']
        form = ProductForm(data=data)
        if not form.is_valid():
            print("Form Errors (rating optional):", form.errors.as_json())
        self.assertTrue(form.is_valid())

    def test_product_form_units_sold_optional(self):
        data = self.valid_data.copy()
        del data['units_sold']
        form = ProductForm(data=data)
        self.assertTrue(form.is_valid())


class StoreViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='viewuser', password='password')
        cls.admin_user = User.objects.create_superuser(username='adminview', password='password', email='admin@test.com')

        cls.spot = FitnessSpot.objects.create(
            pk='viewTestSpotPK',
            name='View Test Spot',
            address='789 View Ln',
            latitude='-6.5200',
            longitude='106.8200'
        )

        cls.product1 = Product.objects.create(name='View Product 1', price=20000, store=cls.spot, image_url='http://example.com/view1.jpg')
        cls.product2 = Product.objects.create(name='View Product 2', price=30000, store=cls.spot, rating='5.0', image_url='http://example.com/view2.jpg')
        cls.product3 = Product.objects.create(name='Expensive Product', price=100000, store=cls.spot, image_url='http://example.com/view3.jpg')

    def setUp(self):
        self.client = Client()

    def test_product_list_view_status_code(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)

    def test_product_list_view_uses_correct_template(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertTemplateUsed(response, 'product_list.html')

    def test_product_list_view_context_data(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertTrue('products' in response.context)
        self.assertTrue('cart_count' in response.context)
        self.assertTrue('fitness_spots' in response.context)

    def test_product_list_pagination(self):
        current_product_count = Product.objects.count()
        needed = 21 - current_product_count
        if needed > 0:
            for i in range(needed):
                 Product.objects.create(name=f'Page Product {i}', price=1000, store=self.spot, image_url=f'http://e.c/page{i}.jpg')

        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(len(response.context['products']), 20)

        response_page2 = self.client.get(reverse('store:product_list') + '?page=2')
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(len(response_page2.context['products']) > 0)

    def test_product_list_search_filter(self):
        response = self.client.get(reverse('store:product_list') + '?q=View Product 1')
        self.assertEqual(response.status_code, 200)
        products_in_context = response.context['products']
        self.assertEqual(len(products_in_context), 1)
        self.assertEqual(products_in_context[0].name, 'View Product 1')

    def test_product_list_sort_price_asc(self):
        response = self.client.get(reverse('store:product_list') + '?sort=price_asc')
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products[0].name, 'View Product 1')
        self.assertEqual(products[1].name, 'View Product 2')
        prices = [p.price for p in products]
        self.assertEqual(prices, sorted(prices))

    def test_product_list_ajax_request(self):
        response = self.client.get(reverse('store:product_list') + '?ajax=1', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_list2.html')
        self.assertNotContains(response, '<title>Store — Produk</title>')

    def test_add_to_cart_requires_post(self):
        response = self.client.get(reverse('store:add_to_cart', args=[self.product1.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_ajax_new_item(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.post(reverse('store:add_to_cart', args=[self.product1.pk]),
                                    {'quantity': 2},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('ditambahkan ke keranjang', data['message'])
        self.assertEqual(data['cart_count'], 1)
        cart = Cart.objects.get(owner=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_ajax_existing_item(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response = self.client.post(reverse('store:add_to_cart', args=[self.product1.pk]),
                                    {'quantity': 3},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)
        item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(item.quantity, 4)

    def test_add_to_cart_non_ajax_redirects(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.post(reverse('store:add_to_cart', args=[self.product1.pk]), {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('store:product_list'))

    def test_view_cart_status_code(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.get(reverse('store:view_cart'))
        self.assertEqual(response.status_code, 200)

    def test_view_cart_uses_correct_template(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.get(reverse('store:view_cart'))
        self.assertTemplateUsed(response, 'checkout.html')

    def test_view_cart_context(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        item1 = CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        item2 = CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        response = self.client.get(reverse('store:view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('cart' in response.context)
        self.assertTrue('items' in response.context)
        self.assertTrue('total' in response.context)
        self.assertEqual(len(response.context['items']), 2)
        expected_total = item1.total_price() + item2.total_price()
        self.assertEqual(response.context['total'], expected_total)

    def test_remove_from_cart_requires_post_ajax(self):
        response_get = self.client.get(reverse('store:remove_from_cart', args=[self.product1.pk]))
        self.assertEqual(response_get.status_code, 405)

        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response_post = self.client.post(reverse('store:remove_from_cart', args=[self.product1.pk]))
        self.assertEqual(response_post.status_code, 400)

    def test_remove_from_cart_ajax(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        response = self.client.post(reverse('store:remove_from_cart', args=[self.product1.pk]),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Item dihapus.')
        self.assertEqual(data['cart_count'], 1)
        self.assertFalse(CartItem.objects.filter(cart=cart, product=self.product1).exists())
        self.assertTrue(CartItem.objects.filter(cart=cart, product=self.product2).exists())
        self.assertIn('Rp', data['grand_total_formatted'])

    def test_update_cart_requires_post_ajax(self):
        response_get = self.client.get(reverse('store:update_cart', args=[self.product1.pk]))
        self.assertEqual(response_get.status_code, 405)

        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response_post = self.client.post(reverse('store:update_cart', args=[self.product1.pk]),
                                         json.dumps({'quantity': 2}), content_type='application/json')
        self.assertEqual(response_post.status_code, 400)

    def test_update_cart_ajax(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        new_quantity = 5
        response = self.client.post(reverse('store:update_cart', args=[self.product1.pk]),
                                    json.dumps({'quantity': new_quantity}), content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('diperbarui', data['message'])
        self.assertFalse(data['removed'])
        self.assertIn('Rp', data['item_total_formatted'])
        self.assertIn('Rp', data['grand_total_formatted'])
        item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(item.quantity, new_quantity)

    def test_update_cart_to_zero_removes_item_ajax(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        response = self.client.post(reverse('store:update_cart', args=[self.product1.pk]),
                                    json.dumps({'quantity': 0}), content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['removed'])
        self.assertIn('dihapus', data['message'])
        self.assertFalse(CartItem.objects.filter(cart=cart, product=self.product1).exists())

    def test_checkout_requires_post_ajax(self):
        response_get = self.client.get(reverse('store:checkout'))
        self.assertEqual(response_get.status_code, 405)

        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response_post = self.client.post(reverse('store:checkout'))
        self.assertEqual(response_post.status_code, 400)

    def test_checkout_ajax_clears_cart(self):
        self.client.login(username='viewuser', password='password')
        cart = Cart.objects.create(owner=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response = self.client.post(reverse('store:checkout'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Checkout berhasil.')
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

    def test_checkout_empty_cart_fails(self):
        self.client.login(username='viewuser', password='password')
        Cart.objects.create(owner=self.user)
        response = self.client.post(reverse('store:checkout'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Keranjang sudah kosong.')

    def _setup_admin_session(self):
        self.client.login(username='adminview', password='password')
        session = self.client.session
        session['is_admin'] = True
        session.save()

    def test_create_product_ajax_requires_admin(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.post(reverse('store:create_product_ajax'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_create_product_ajax_success(self):
        self._setup_admin_session()
        product_data = {
            'name': 'Admin Created Product',
            'price': 15000,
            'image_url': 'http://example.com/admin.jpg',
            'store': self.spot.pk
        }
        response = self.client.post(reverse('store:create_product_ajax'), product_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('berhasil ditambahkan', data['message'])
        self.assertTrue(Product.objects.filter(pk=data['product_id']).exists())

    def test_create_product_ajax_invalid_data(self):
        self._setup_admin_session()
        invalid_data = { 'name': 'Incomplete' }
        response = self.client.post(reverse('store:create_product_ajax'), invalid_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertTrue('errors' in data)
        self.assertIn('price', data['errors'])
        self.assertIn('image_url', data['errors'])
        self.assertIn('store', data['errors'])

    def test_edit_product_get_requires_admin(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.get(reverse('store:edit_product', args=[self.product1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('central:login') in response.url)

    def test_edit_product_get_ajax_success(self):
        self._setup_admin_session()
        response = self.client.get(reverse('store:edit_product', args=[self.product1.pk]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_product2.html')
        self.assertContains(response, 'value="View Product 1"')

    def test_edit_product_post_ajax_success(self):
        self._setup_admin_session()
        updated_data = {
            'name': 'Updated Product Name',
            'price': self.product1.price,
            'image_url': self.product1.image_url,
            'store': self.product1.store.pk,
            'rating': self.product1.rating if self.product1.rating else '',
            'units_sold': self.product1.units_sold if self.product1.units_sold else ''
        }
        response = self.client.post(reverse('store:edit_product', args=[self.product1.pk]), updated_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Produk berhasil diperbarui!')
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Updated Product Name')

    def test_edit_product_post_ajax_invalid(self):
        self._setup_admin_session()
        invalid_data = {
            'name': '',
            'price': self.product1.price,
            'image_url': self.product1.image_url,
            'store': self.product1.store.pk,
            'rating': self.product1.rating if self.product1.rating else '',
            'units_sold': self.product1.units_sold if self.product1.units_sold else ''
        }
        response = self.client.post(reverse('store:edit_product', args=[self.product1.pk]), invalid_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'This field is required.', status_code=400)

    def test_delete_product_requires_admin_post_ajax(self):
        response_get = self.client.get(reverse('store:delete_product', args=[self.product1.pk]))
        self.assertEqual(response_get.status_code, 405)

        self.client.login(username='viewuser', password='password')
        response_user = self.client.post(reverse('store:delete_product', args=[self.product1.pk]),
                                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_user.status_code, 403)

        self._setup_admin_session()
        response_non_ajax = self.client.post(reverse('store:delete_product', args=[self.product1.pk]))
        self.assertEqual(response_non_ajax.status_code, 400)

    def test_delete_product_ajax_success(self):
        self._setup_admin_session()
        product_to_delete = Product.objects.create(name='Delete Me', price=100, store=self.spot, image_url='http://e.c/del.jpg')
        product_pk = product_to_delete.pk
        response = self.client.post(reverse('store:delete_product', args=[product_pk]),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('berhasil dihapus', data['message'])
        self.assertFalse(Product.objects.filter(pk=product_pk).exists())

    def test_view_product_detail_requires_login(self):
        response = self.client.get(reverse('store:view_product_detail', args=[self.product1.pk]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Anda harus login', data['error'])

    def test_view_product_detail_success_ajax(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.get(reverse('store:view_product_detail', args=[self.product1.pk]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_product_detail.html')
        self.assertTrue('product' in response.context)
        self.assertEqual(response.context['product'], self.product1)

    def test_view_product_detail_non_ajax_redirects(self):
        self.client.login(username='viewuser', password='password')
        response = self.client.get(reverse('store:view_product_detail', args=[self.product1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('store:product_list'))