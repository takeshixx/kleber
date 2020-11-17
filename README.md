# Kleber

Kleber is a paste and file sharing platform that allows to remove metadata from uploaded files. E.g. removing EXIF data from uploaded images. If features a REST-API with an official [kleber-cli](https://github.com/takeshixx/kleber-cli).

Additional features:

* Syntax highlighting
* Client-side paste encryption
* Password protection for uplodaded files
* Upload history for logged-in users
* Login via GitHub

## Example Configuration

The included [settings.py](https://github.com/takeshixx/kleber/blob/master/kleber/settings.py) configures everything that is required by Kleber. It is suited for local development setups where it just uses a SQLite database. To configure a production setup, the file `kleber/local_settings_prod.py` should be added. The following listing shows an example of such a file, where all settings can be overwritten:

```python
from kleber import kleber_secrets

DEBUG = False
ALLOWED_HOSTS = ['kleber.io',
                 'www.kleber.io']
SITE_URL = 'https://kleber.io'
SITE_ID = 3
EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25
UPLOAD_PATH = '/var/www/uploads/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': kleber_secrets.DB_DATABASE,
        'USER': kleber_secrets.DB_USER,
        'PASSWORD': kleber_secrets.DB_PASSWORD,
        'HOST': kleber_secrets.DB_HOST,
        'PORT': kleber_secrets.DB_PORT,
    }
}
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'],
    'PAGE_SIZE': 10
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/www/logs/kleber.log',
        },
        'mail_admins': {
            'level': 'INFO',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'management_commands': {
            'handlers': ['mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

The example above shows the recommended way of handling secrets. All secrets are stored in `kleber/kleber_secrets.py` which must not be commited to any repository. The following listing shows an example file:

```python
SECRET_KEY = '...'

EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'info@kleber.io'
EMAIL_HOST_PASSWORD = "..."

DB_DATABASE = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = '...'
DB_HOST = '127.0.0.1'
DB_PORT = 5432
```