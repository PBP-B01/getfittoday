# store/forms.py
from django import forms
from .models import Product
from home.models import FitnessSpot

class ProductForm(forms.ModelForm):
    """Form untuk membuat dan mengedit Produk."""

    store = forms.ModelChoiceField(
        queryset=FitnessSpot.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'
        }),
        label="Toko (Fitness Spot)",
        empty_label="-- Pilih Toko --"
    )

    class Meta:
        model = Product
        fields = ['name', 'price', 'rating', 'units_sold', 'image_url', 'store']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white',
                'placeholder': 'Masukkan nama produk'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white',
                'placeholder': 'Masukkan harga produk (contoh: 50000)',
                'min': '0',
                'step': '1'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white',
                'placeholder': 'Rating (opsional, 0-5, contoh: 4.5)',
                'step': '0.1',
                'min': '0',
                'max': '5'
            }),
            'units_sold': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white',
                'placeholder': 'Jumlah terjual (opsional, contoh: 100 atau 1rb+)'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white',
                'placeholder': 'https://example.com/image.jpg'
            }),
        }
        labels = {
            'name': 'Nama Produk',
            'price': 'Harga (Rp)',
            'rating': 'Rating',
            'units_sold': 'Jumlah Terjual',
            'image_url': 'URL Gambar',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['store'].queryset = FitnessSpot.objects.all().order_by('name')
        self.fields['name'].required = True
        self.fields['price'].required = True
        self.fields['image_url'].required = True
        self.fields['store'].required = True
        self.fields['rating'].required = False
        self.fields['units_sold'].required = False

    def clean_price(self):
        """Validasi harga tidak boleh negatif"""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Harga tidak boleh negatif.')
        return price
    
    def clean_rating(self):
        """Validasi rating antara 0-5"""
        rating = self.cleaned_data.get('rating')

        if rating is not None:
            try:
                rating_float = float(rating) 
            except (ValueError, TypeError):
                raise forms.ValidationError('Masukkan nilai rating numerik yang valid.')

            if rating_float < 0.0 or rating_float > 5.0:
                 raise forms.ValidationError('Rating harus antara 0.0 dan 5.0.')
            

            return rating_float 

        return rating