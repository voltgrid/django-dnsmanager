import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_app.settings'
test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, test_dir)

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=False)
    failures = test_runner.run_tests([])
    sys.exit(bool(failures))

if __name__ == '__main__':
    runtests()
