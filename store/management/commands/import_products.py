import pandas as pd
from django.core.management.base import BaseCommand
from store.models import Product
import os
import random
from home.models import FitnessSpot
from django.db import connection

class Command(BaseCommand):
    help = 'Imports products from an Excel file into the database'

    def handle(self, *args, **options):
        file_name = 'product_dataset.xlsx'
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
        
        self.stdout.write('Mengambil data fitness spots...')
        spot_pks = list(FitnessSpot.objects.values_list('pk', flat=True))

        if not spot_pks:
            self.stdout.write(self.style.ERROR('Tidak ada data FitnessSpot di database! Harap muat data GOR terlebih dahulu.'))
            return
            
        self.stdout.write(f'Ditemukan {len(spot_pks)} fitness spots (toko).')
        
        self.stdout.write('Deleting old products and resetting ID sequence...')
        
        table_name = Product._meta.db_table
        db_vendor = connection.vendor

        try:
            with connection.cursor() as cursor:
                if db_vendor == 'sqlite':

                    cursor.execute(f"DELETE FROM {table_name};")

                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
                
                elif db_vendor == 'postgresql':
                    cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
                    
                elif db_vendor == 'mysql':
                    cursor.execute(f"TRUNCATE TABLE {table_name};")
                    
                else:
                    self.stdout.write(self.style.WARNING(f"Using standard Django delete (PK might not reset for '{db_vendor}')..."))
                    Product.objects.all().delete()

            self.stdout.write(self.style.SUCCESS('Old products deleted and ID sequence reset.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deleting/resetting data: {e}'))
            return

        
        self.stdout.write('Importing new products...')
        
        products_to_create = []
        
        for index, row in df.iterrows():
            rating_val = row['Rating'] if row['Rating'] != 'N/A' else None
            sold_val = row['Units Sold'] if row['Units Sold'] != 'N/A' else None

            chosen_store_id = random.choice(spot_pks) 

            product = Product(
                name=row['Product Name'],
                price=row['Price (Rp)'],
                rating=rating_val,
                units_sold=sold_val,
                image_url=row['Image URL'],
                store_id = chosen_store_id 
            )
            products_to_create.append(product)

        Product.objects.bulk_create(products_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(products_to_create)} products.'))