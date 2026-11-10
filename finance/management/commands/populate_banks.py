from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import Bank, BANKS
import os
import shutil


class Command(BaseCommand):
    help = 'Populate predefined Russian banks'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.BASE_DIR / 'static'
        media_banks_dir = os.path.join(settings.MEDIA_ROOT, 'banks')
        os.makedirs(media_banks_dir, exist_ok=True)

        for bank_name, image_name in BANKS:
            source_path = os.path.join(static_dir, 'banks', image_name)
            media_path = os.path.join(media_banks_dir, image_name)
            bank, created = Bank.objects.get_or_create(name=bank_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created bank: {bank_name}')
            if os.path.exists(source_path):
                if not os.path.exists(media_path):
                    shutil.copyfile(source_path, media_path)
                bank.image = f'banks/{image_name}'
                bank.save(update_fields=['image'])
                updated_count += 1
                self.stdout.write(f'Updated image for: {bank_name}')
            else:
                self.stdout.write(f'No image found for: {bank_name}')
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} banks, updated {updated_count} images'))
