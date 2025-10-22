import pandas as pd
from django.core.management.base import BaseCommand
from store.models import Product  # Sesuaikan dengan nama app dan model Anda
import os

class Command(BaseCommand):
    help = 'Imports products from an Excel file into the database'

    def handle(self, *args, **options):     
        # Masukkin nama file excelnya
        file_name = 'tokopedia_data_bola+basket.xlsx' 
        
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), file_name)

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading from {file_path}...'))
        
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading Excel file: {e}'))
            return

        # Hapus semua produk lama biar gaada duplikat setiap kali impor
        self.stdout.write('Deleting old products...')
        Product.objects.all().delete()
        self.stdout.write('Old products deleted.')

        self.stdout.write('Importing new products...')
        
        products_to_create = []
        
        # Loop melalui setiap baris di DataFrame Excel
        for index, row in df.iterrows():
            
            # Ambil data dan bersihkan 'N/A' kalo ada
            rating_val = row['Rating'] if row['Rating'] != 'N/A' else None
            sold_val = row['Units Sold'] if row['Units Sold'] != 'N/A' else None
            
            # Buat objek Product
            product = Product(
                name=row['Product Name'],
                price=row['Price (Rp)'],
                rating=rating_val,
                units_sold=sold_val,
                image_url=row['Image URL']
            )
            products_to_create.append(product)

        # Simpan semua produk ke database
        Product.objects.bulk_create(products_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(products_to_create)} products.'))