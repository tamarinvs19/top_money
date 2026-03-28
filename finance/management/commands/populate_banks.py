from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import Bank, RUSSIAN_BANKS
import os


class Command(BaseCommand):
    help = 'Populate predefined Russian banks'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for bank_name, image_name in RUSSIAN_BANKS:
            image_path = os.path.join(settings.MEDIA_ROOT, 'banks', image_name)
            bank, created = Bank.objects.get_or_create(name=bank_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created bank: {bank_name}')
            if os.path.exists(image_path):
                bank.image = f'banks/{image_name}'
                bank.save(update_fields=['image'])
                updated_count += 1
                self.stdout.write(f'Updated image for: {bank_name}')
            else:
                self.stdout.write(f'No image found for: {bank_name}')
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} banks, updated {updated_count} images'))
