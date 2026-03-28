from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import Provider, PROVIDERS
import os


class Command(BaseCommand):
    help = 'Populate predefined providers'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for provider_name, image_name in PROVIDERS:
            image_path = os.path.join(settings.MEDIA_ROOT, 'providers', image_name)
            provider, created = Provider.objects.get_or_create(name=provider_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created provider: {provider_name}')
            if os.path.exists(image_path):
                provider.image = f'providers/{image_name}'
                provider.save(update_fields=['image'])
                updated_count += 1
                self.stdout.write(f'Updated image for: {provider_name}')
            else:
                self.stdout.write(f'No image found for: {provider_name}')
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} providers, updated {updated_count} images'))
