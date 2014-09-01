print('Loaded %s' % __file__)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'dnsmanager',
    'test_app',
)

SECRET_KEY = '_'
SITE_ID = 1
ROOT_URLCONF = 'test_app.urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

DNS_MANAGER_DOMAIN_MODEL = 'test_app.Domain'