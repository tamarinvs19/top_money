from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import Bank, Provider, BANKS, PROVIDERS
import os


class Command(BaseCommand):
    help = 'Generate SVG logos for banks and providers with brand colors'

    BANK_COLORS = {
        'Sberbank': '#3db46d',
        'T-Bank': '#ffdb00',
        'Alfa-Bank': '#e20613',
        'VTB': '#2d86c3',
        'Gazprombank': '#8a2be2',
        'Rosselkhozbank': '#00a651',
        'Otkritie': '#0078d7',
        'Raiffeisenbank': '#ffdb00',
        'MKB': '#ff6600',
        'UniCredit Bank': '#003d7c',
        'PSBank': '#004f9f',
        'Russian Standard Bank': '#ff0000',
        'MTS Bank': '#e2001a',
        'BIN': '#00347c',
        'Ozon Bank': '#005bff',
        'Yandex Bank': '#ff0000',
        'BCS Bank': '#00bfff',
        'DOM.RF Bank': '#90ee90',
        'Svoi Bank': '#00b4d9',
    }

    BANK_SHORT_NAMES = {
        'Sberbank': 'SBER',
        'MTS Bank': 'MTS',
        'BCS Bank': 'BCS',
        'DOM.RF Bank': 'DOM',
        'Gazprombank': 'GPB',
    }

    PROVIDER_COLORS = {
        'Qiwi': '#ff4800',
        'WebMoney': '#036cb5',
        'Finuslugi': '#00aace',
        'Alibaba': '#ff6a00',
    }

    def handle(self, *args, **options):
        self.generate_bank_logos()
        self.generate_provider_logos()

    def generate_bank_logos(self):
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        banks_dir = os.path.join(static_dir, 'banks')
        os.makedirs(banks_dir, exist_ok=True)

        for bank_name, image_name in BANKS:
            image_path = os.path.join(banks_dir, image_name.replace('.png', '.svg'))
            color = self.BANK_COLORS.get(bank_name, '#1e88e5')
            short_name = self.BANK_SHORT_NAMES.get(bank_name)
            
            svg_content = self.create_svg(bank_name, color, short_name)
            with open(image_path, 'w') as f:
                f.write(svg_content)
            
            bank, _ = Bank.objects.get_or_create(name=bank_name)
            bank.image = f'banks/{image_name.replace(".png", ".svg")}'
            bank.save(update_fields=['image'])
            self.stdout.write(f'Generated: {bank_name} -> {image_name.replace(".png", ".svg")}')

    def generate_provider_logos(self):
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        providers_dir = os.path.join(static_dir, 'providers')
        os.makedirs(providers_dir, exist_ok=True)

        for provider_name, image_name in PROVIDERS:
            image_path = os.path.join(providers_dir, image_name.replace('.png', '.svg'))
            color = self.PROVIDER_COLORS.get(provider_name, '#9c27b0')
            
            svg_content = self.create_svg(provider_name, color)
            with open(image_path, 'w') as f:
                f.write(svg_content)
            
            provider, _ = Provider.objects.get_or_create(name=provider_name)
            provider.image = f'providers/{image_name.replace(".png", ".svg")}'
            provider.save(update_fields=['image'])
            self.stdout.write(f'Generated: {provider_name} -> {image_name.replace(".png", ".svg")}')

    def create_svg(self, name, color, short_name=None):
        if short_name:
            text = short_name
        else:
            words = name.split()
            if len(words) == 1:
                if len(name) <= 3:
                    text = name.upper()
                else:
                    text = name[:3].upper()
            else:
                text = ''.join([w[0] for w in words if w and w[0].isupper()])[:3]
                if len(text) < 2:
                    text = words[0][:3].upper()
        
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="{color}"/>
  <text x="64" y="78" font-family="Arial, Helvetica, sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle">{text}</text>
</svg>'''
