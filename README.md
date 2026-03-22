# Top Money - Personal Finance Manager

A Django-based web application for managing personal finances with support for multiple asset types, transactions, and import/export functionality.

## Features

- **Multi-asset management**: Support for cash, debit/credit cards, deposits, e-wallets, brokerage accounts, and savings accounts
- **Transaction tracking**: Record refills (income), waste (expenses), and transfers between assets
- **Category-based organization**: Predefined categories for expenses and income
- **Import/Export**: Load transactions from Excel (.xlsx) or CSV files, export to Excel
- **User authentication**: Secure account management with Django's built-in auth system

## Requirements

- Python 3.10+
- Django 4.2+
- Gunicorn (for production)

## Project Structure

```
top_money/
├── config/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── finance/          # Main application
│   ├── models.py     # Data models
│   ├── views.py      # Views
│   └── ...
├── templates/        # HTML templates
├── docs/             # Documentation
├── manage.py
└── requirements.txt
```

## Development Setup

### 1. Clone and create virtual environment

```bash
git clone <repository-url>
cd top_money
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the project root:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

Generate a secure secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Initialize database

```bash
python manage.py migrate
```

### 5. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run development server

```bash
python manage.py runserver
```

Visit http://localhost:8000 in your browser.

## Production Deployment

### 1. Install Gunicorn

```bash
pip install gunicorn
```

### 2. Configure environment

| Variable | Description | Required |
|----------|-------------|----------|
| `DJANGO_SECRET_KEY` | Secret key for cryptographic signing | Yes |
| `DJANGO_DEBUG` | Debug mode (`True`/`False`) | No (default: False) |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF trusted origins | Yes |
| `DJANGO_FORCE_SCRIPT_NAME` | Subdirectory prefix (optional) | No |

### Example production `.env`:

```bash
DJANGO_SECRET_KEY=your-production-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
```

### 3. Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Start the server

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Reverse Proxy (Recommended)

For production, use a reverse proxy like Nginx:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/top_money/staticfiles/;
    }
}
```

## Asset Types

| Type | Description |
|------|-------------|
| `CASH` | Physical cash |
| `DEBIT_CARD` | Debit card (bank account) |
| `DEPOSIT` | Bank deposit |
| `CREDIT_CARD` | Credit card |
| `E_WALLET` | Electronic wallet (Qiwi, Yandex Money) |
| `BROKERAGE` | Investment/brokerage account |
| `SAVING_ACCOUNT` | Savings account |

## Transaction Types

| Type | Description |
|------|-------------|
| `REFILL` | Money coming in (income, deposit) |
| `WASTE` | Money going out (expense) |
| `TRANSFER` | Money between assets |

## Import/Export

See [docs/import_export.md](docs/import_export.md) for detailed import/export format specifications.

### Quick Guide

1. **Import**: Go to Profile → Load Transactions, select Excel/CSV file
2. **Export**: Go to Profile → Download Transactions for Excel export

## Documentation

- [Data Models](docs/models.md) - Detailed model specifications
- [Import/Export Format](docs/import_export.md) - File format for data import

## License

MIT
