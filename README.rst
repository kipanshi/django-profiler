=================================
 Profiling django view functions
=================================

The default profiler is cPython.

Profiling is done via management command.
TODO: Currently class-based views are not supported

Installation
============

Download and run
    python setup.py install

For flexibility, it's a good practice to use `local_settings.py`
module for local settings.

Register app in your `local_settings.py`

    INSTALLED_APPS += (
        'profiler',
    )

Set up the following options according to your project:

    # In case you use OneToOne with 
    # you need to specify it explicitly.
    # If this option is not set, `django.contrib.auth.models.User`
    # is used by default
    PROFILER_USER_MODEL = 'yourapp.models.User'
    PROFILER_LIMIT = 30  # by default output first 30 stats cProfile results
    PROFILER_QUERIES_LIMIT = 3  # output by default 3 slowest queries


Usage
=====

**NOTE: If your view is decorated, LineProfiler will output stats for the top
decorator, so it's recomended temporarily disable decorators if you want
to profile your view with LineProfiler**

Assuming you have a view function named
``user_details(request, translator_id)`` in the app ``account``:

    ./manage.py profile_view --prefix=account.views user_details:7 --profiler=cProfile,LineProfiler
Here ``7`` is an argument to user_details function.

For help:

    ./manage.py help profile_view

If you want to use LineProfiler, install it:

    pip install line_profiler

If you want to store contents in a file:

    yes y | ./manage.py profile_view --prefix=account.views user_details:7 --profiler=cProfile,LineProfiler > user_details_7_profiling_results.txt
