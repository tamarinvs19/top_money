from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import CashbackCategory, WasteCategory
import os


class Command(BaseCommand):
    help = 'Populate CashbackCategory table with default categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Products', 'image': 'cashback_categories/products.svg', 'waste_category': WasteCategory.PRODUCTS},
            {'name': 'Cafe and restaurants', 'image': 'cashback_categories/cafe_and_restaurants.svg', 'waste_category': WasteCategory.CAFE_AND_RESTAURANTS},
            {'name': 'Transport', 'image': 'cashback_categories/transport.svg', 'waste_category': WasteCategory.TRANSPORT},
            {'name': 'HCS', 'image': 'cashback_categories/hcs.svg', 'waste_category': WasteCategory.HCS},
            {'name': 'Household', 'image': 'cashback_categories/household.svg', 'waste_category': WasteCategory.HOUSEHOLD},
            {'name': 'Personal', 'image': 'cashback_categories/personal.svg', 'waste_category': WasteCategory.PERSONAL},
            {'name': 'Leisure', 'image': 'cashback_categories/leisure.svg', 'waste_category': WasteCategory.LEISURE},
            {'name': 'Entertainment', 'image': 'cashback_categories/entertainment.svg', 'waste_category': WasteCategory.ENTERTAINMENT},
            {'name': 'Clothing and shoes', 'image': 'cashback_categories/clothing_and_shoes.svg', 'waste_category': WasteCategory.CLOTHING_AND_SHOES},
            {'name': 'Sport', 'image': 'cashback_categories/sport.svg', 'waste_category': WasteCategory.SPORT},
            {'name': 'Health and beauty', 'image': 'cashback_categories/health_and_beauty.svg', 'waste_category': WasteCategory.HEALTH_AND_BEAUTY},
            {'name': 'Subscriptions', 'image': 'cashback_categories/subscriptions.svg', 'waste_category': WasteCategory.SUBSCRIPTIONS},
            {'name': 'Taxes and penalties', 'image': 'cashback_categories/taxes_and_penalties.svg', 'waste_category': WasteCategory.TAXES_AND_PENALTIES},
            {'name': 'Learning', 'image': 'cashback_categories/learning.svg', 'waste_category': WasteCategory.LEARNING},
            {'name': 'Gifts', 'image': 'cashback_categories/gifts.svg', 'waste_category': WasteCategory.GIFTS},
            {'name': 'Technique', 'image': 'cashback_categories/technique.svg', 'waste_category': WasteCategory.TECHNIQUE},
            {'name': 'Traveling', 'image': 'cashback_categories/traveling.svg', 'waste_category': WasteCategory.TRAVELING},
            {'name': 'Realty', 'image': 'cashback_categories/realty.svg', 'waste_category': WasteCategory.REALTY},
            {'name': 'Online stores', 'image': 'cashback_categories/online_stores.svg', 'waste_category': None},
            {'name': 'Apps and games', 'image': 'cashback_categories/apps_and_games.svg', 'waste_category': None},
            {'name': 'Other', 'image': 'cashback_categories/other.svg', 'waste_category': WasteCategory.OTHER},
        ]

        created_count = 0
        updated_count = 0
        for cat_data in categories:
            image_path = os.path.join(settings.STATIC_ROOT, cat_data['image'])
            obj, created = CashbackCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'image': cat_data['image'],
                    'waste_category': cat_data['waste_category'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat_data["name"]}'))
            else:
                if os.path.exists(image_path):
                    updated_count += 1
                    obj.image = cat_data['image'];
                    obj.save()
                    self.stdout.write(f'Category already exists: {cat_data["name"]}, updated image')
                else:
                    self.stdout.write(f'No image found for: {cat_data["name"]} --> {image_path}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {created_count} categories created, {updated_count} updated'))
