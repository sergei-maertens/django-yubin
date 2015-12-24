#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

import os
import sys


def runtests(*args):
    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

    import django
    from django.test.utils import get_runner
    from django.conf import settings

    django.setup()  # only 1.7 and up are supported

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, failfast=False)
    failures = test_runner.run_tests(args)
    sys.exist(failures)


if __name__ == '__main__':
    # TODO: forward sys.argv?
    runtests()
