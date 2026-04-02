from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import CashbackCategory, CASHBACK_CATEGORIES
import os


class Command(BaseCommand):
    help = 'Populate CashbackCategory table with default categories'

    def handle(self, *args, **options):
        category_map = dict(CASHBACK_CATEGORIES)

        created_count = 0
        updated_count = 0
        for key, label in CASHBACK_CATEGORIES:
            image_name = key.lower() + '.svg'
            image_path = os.path.join(settings.STATIC_ROOT, 'cashback_categories', image_name)
            
            obj, created = CashbackCategory.objects.get_or_create(
                name=label,
                defaults={
                    'image': f'cashback_categories/{image_name}',
                    'waste_category': None,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {label}'))
            else:
                if os.path.exists(image_path):
                    updated_count += 1
                    obj.image = f'cashback_categories/{image_name}'
                    obj.save()
                    self.stdout.write(f'Category already exists: {label}, updated image')
                else:
                    self.stdout.write(f'No image found for: {label} --> {image_path}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {created_count} categories created, {updated_count} updated'))
