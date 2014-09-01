from setuptools import setup, find_packages

VERSION = '0.0.1'

setup(
    name='django-dnsmanager',
    version=VERSION,
    description='Reusable Django app that provides DNS Zone editing and management',
    long_description=open('README.md').read(),
    author='Andrew Cutler',
    author_email='andrew@voltgrid.com',
    url='https://github.com/voltgrid/django-dnsmanager',
    package_dir={'dnsmanager': 'dnsmanager'},
    packages=find_packages(),
    package_data = {
        # If any package contains *.txt etc include
        '': ['*.txt', '*.html', '*.md'],
    },
    classifiers=['Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: System :: Systems Administration'
    ],
    install_requires=[
        'Django',
        'dnspython',
        'django-reversion'
    ],
)
