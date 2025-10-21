import json
from django.core.management.base import BaseCommand
from django.db import transaction
# Diubah dari 'spots' menjadi 'home' agar sesuai dengan nama aplikasi Anda
from home.models import FitnessSpot, PlaceType

class Command(BaseCommand):
    help = 'Memuat data tempat kebugaran dari file JSON ke dalam basis data'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path ke file JSON yang akan diimpor')

    @transaction.atomic # Memastikan semua operasi basis data berhasil atau tidak sama sekali
    def handle(self, *args, **options):
        json_file_path = options['json_file']
        self.stdout.write(self.style.SUCCESS(f"Memulai impor dari '{json_file_path}'..."))

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Error: File tidak ditemukan di '{json_file_path}'"))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Error: Gagal mendekode JSON dari file."))
            return

        created_count = 0
        updated_count = 0

        for place_data in data:
            # Siapkan data dasar untuk model FitnessSpot
            defaults = {
                'name': place_data.get('displayName', {}).get('text', 'Nama tidak tersedia'),
                'address': place_data.get('formattedAddress', ''),
                'phone_number': place_data.get('nationalPhoneNumber'),
                'website': place_data.get('websiteUri'),
                'latitude': place_data.get('location', {}).get('latitude'),
                'longitude': place_data.get('location', {}).get('longitude'),
                'rating': place_data.get('rating'),
                'rating_count': place_data.get('userRatingCount', 0),
            }

            # Gunakan update_or_create untuk menghindari duplikasi berdasarkan place_id
            spot, created = FitnessSpot.objects.update_or_create(
                place_id=place_data['id'],
                defaults=defaults
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            # Tangani hubungan ManyToManyField untuk 'types'
            place_types_from_json = place_data.get('types', [])
            type_objects = []
            for type_name in place_types_from_json:
                # Dapatkan atau buat objek PlaceType untuk setiap jenis
                type_obj, _ = PlaceType.objects.get_or_create(name=type_name)
                type_objects.append(type_obj)
            
            # Atur hubungan ManyToMany, ini akan menimpa yang lama
            if type_objects:
                spot.types.set(type_objects)

        self.stdout.write(self.style.SUCCESS(
            f"Impor selesai! {created_count} tempat baru dibuat, {updated_count} tempat diperbarui."
        ))

### Langkah-langkah Selanjutnya

# 1.  **Perubahan Kode**: Satu-satunya perubahan yang saya buat di dalam Canvas adalah mengubah `from spots.models` menjadi `from home.models` agar cocok dengan nama aplikasi Anda (`home`).

# 2.  **Buat Direktori**: Di dalam aplikasi `home` Anda, buat direktori baru seperti ini. Anda mungkin perlu membuat folder `management` dan `commands` secara manual.
#     ```
#     home/
#     └── management/
#         └── commands/
#     ```

# 3.  **Simpan File**: Simpan file `import_spots.py` dari Canvas ke dalam direktori `commands` yang baru saja Anda buat. Struktur akhir Anda akan terlihat seperti ini:
#     ```
#     home/
#     ├── management/
#     │   └── commands/
#     │       └── import_spots.py
#     ├── models.py
#     └── ... (file lainnya)
    

