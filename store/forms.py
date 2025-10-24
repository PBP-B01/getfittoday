# store/forms.py
from django import forms
from .models import Product
from home.models import FitnessSpot

class ProductForm(forms.ModelForm):
    """Form untuk membuat dan mengedit Produk."""

    store = forms.ModelChoiceField(
        queryset=FitnessSpot.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'
        }),
        label="Toko (Fitness Spot)"
    )

    class Meta:
        model = Product
        fields = ['name', 'price', 'rating', 'units_sold', 'image_url', 'store']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'}),
            'price': forms.NumberInput(attrs={'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'}),
            'rating': forms.TextInput(attrs={'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'}),
            'units_sold': forms.TextInput(attrs={'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'}),
            'image_url': forms.URLInput(attrs={'class': 'block w-full rounded-md border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2 px-3 text-black bg-white'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['store'].queryset = FitnessSpot.objects.all()

