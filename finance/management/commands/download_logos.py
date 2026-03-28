from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import Bank, Provider, BANKS, PROVIDERS
import os
import requests
from urllib.parse import urljoin


class Command(BaseCommand):
    help = 'Download bank and provider logos from toplogos.ru'

    TOPLOGOS_BASE = 'https://toplogos.ru/images'

    BANK_URLS = {
        'Sberbank': '/logo-sber.png',
        'T-Bank': '/logo-tbank.png',
        'Alfa-Bank': '/logo-alfa-bank.png',
        'VTB': '/logo-vtb.png',
        'Gazprombank': '/logo-gazprombank.png',
        'Rosselkhozbank': '/logo-rosselhozbank.png',
        'Otkritie': '/logo-otkritie-bank.png',
        'Raiffeisenbank': '/logo-raiffeisenbank.png',
        'MKB': '/logo-mkb.png',
        'UniCredit Bank': '/logo-unicredit-bank.png',
        'PSBank': '/logo-psbank.png',
        'Russian Standard Bank': '/logo-russian-standard.png',
        'MTS Bank': '/logo-mts-bank.png',
        'BIN': '/logo-binbank.png',
        'Ozon Bank': '/logo-ozon-bank.png',
        'Yandex Bank': '/logo-yandex-bank.png',
        'BCS Bank': '/logo-bcs-bank.png',
        'DOM.RF Bank': '/logo-domrf.png',
        'Svoi Bank': '/logo-svoi-bank.png',
    }

    PROVIDER_URLS = {
        'Qiwi': '/logo-qiwi.png',
        'WebMoney': '/logo-webmoney.png',
        'Finuslugi': '/logo-finuslugi.png',
        'Alibaba': '/logo-alibaba.png',
    }

    def handle(self, *args, **options):
        self.download_bank_logos()
        self.download_provider_logos()
        self.update_models()

    def get_download_url(self, page_url):
        try:
            response = requests.get(urljoin(self.TOPLOGOS_BASE, page_url), timeout=10)
            if response.status_code == 200:
                text = response.text
                download_link_start = text.find('/download/')
                if download_link_start != -1:
                    download_link_end = text.find('"', download_link_start)
                    if download_link_end != -1:
                        return text[download_link_start:download_link_end]
        except Exception as e:
            self.stdout.write(f'Error fetching {page_url}: {e}')
        return None

    def download_image(self, url, save_path):
        try:
            full_url = urljoin(self.TOPLOGOS_BASE, url)
            response = requests.get(full_url, timeout=30)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            self.stdout.write(f'Error downloading {url}: {e}')
        return False

    def download_bank_logos(self):
        banks_dir = os.path.join(settings.MEDIA_ROOT, 'banks')
        os.makedirs(banks_dir, exist_ok=True)

        for bank_name, image_name in BANKS:
            image_path = os.path.join(banks_dir, image_name)
            if os.path.exists(image_path):
                self.stdout.write(f'Skipping existing: {image_name}')
                continue

            page_url = self.BANK_URLS.get(bank_name)
            if not page_url:
                self.generate_svg_placeholder(bank_name, 'banks', image_name)
                continue

            download_url = self.get_download_url(page_url)
            if download_url:
                if self.download_image(download_url, image_path):
                    self.stdout.write(f'Downloaded: {bank_name} -> {image_name}')
                else:
                    self.generate_svg_placeholder(bank_name, 'banks', image_name)
            else:
                self.generate_svg_placeholder(bank_name, 'banks', image_name)

    def download_provider_logos(self):
        providers_dir = os.path.join(settings.MEDIA_ROOT, 'providers')
        os.makedirs(providers_dir, exist_ok=True)

        for provider_name, image_name in PROVIDERS:
            image_path = os.path.join(providers_dir, image_name)
            if os.path.exists(image_path):
                self.stdout.write(f'Skipping existing: {image_name}')
                continue

            page_url = self.PROVIDER_URLS.get(provider_name)
            if not page_url:
                self.generate_svg_placeholder(provider_name, 'providers', image_name)
                continue

            download_url = self.get_download_url(page_url)
            if download_url:
                if self.download_image(download_url, image_path):
                    self.stdout.write(f'Downloaded: {provider_name} -> {image_name}')
                else:
                    self.generate_svg_placeholder(provider_name, 'providers', image_name)
            else:
                self.generate_svg_placeholder(provider_name, 'providers', image_name)

    def update_models(self):
        for bank_name, image_name in BANKS:
            bank = Bank.objects.filter(name=bank_name).first()
            if bank and not bank.image:
                image_path = f'banks/{image_name}'
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    bank.image = image_path
                    bank.save(update_fields=['image'])
                    self.stdout.write(f'Updated bank model: {bank_name}')
                else:
                    self.generate_svg_placeholder(bank_name, 'banks', image_name)

        for provider_name, image_name in PROVIDERS:
            provider = Provider.objects.filter(name=provider_name).first()
            if provider and not provider.image:
                image_path = f'providers/{image_name}'
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    provider.image = image_path
                    provider.save(update_fields=['image'])
                    self.stdout.write(f'Updated provider model: {provider_name}')
                else:
                    self.generate_svg_placeholder(provider_name, 'providers', image_name)

    def generate_svg_placeholder(self, name, folder, image_name):
        svg_dir = os.path.join(settings.MEDIA_ROOT, folder)
        os.makedirs(svg_dir, exist_ok=True)
        
        svg_path = os.path.join(svg_dir, image_name.replace('.png', '.svg'))
        
        initials = ''.join([w[0] for w in name.split() if w]).upper()[:2]
        
        colors = ['#1e88e5', '#43a047', '#e53935', '#fb8c00', '#8e24aa', '#00acc1', '#3949ab', '#d81b60']
        color = colors[hash(name) % len(colors)]
        
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="16" fill="{color}"/>
  <text x="64" y="78" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle">{initials}</text>
</svg>'''
        
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        model_class = Bank if folder == 'banks' else Provider
        model = model_class.objects.filter(name=name).first()
        if model:
            model.image = f'{folder}/{image_name.replace(".png", ".svg")}'
            model.save(update_fields=['image'])
            self.stdout.write(f'Generated SVG placeholder for: {name}')
