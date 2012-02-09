from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import client
from django.conf import settings
from django.db import connection
from profiler.sqlprinting import SqlPrintingMiddleware

from profiler import PROFILER_LIMIT, PROFILERS, profile


class Command(BaseCommand):
    args = '<view_name[:arg1[,arg2]] view_name[:arg1[,arg2]] ...>'
    help = "Profile views with cProfile."
    option_list = BaseCommand.option_list + (
        make_option('--prefix', dest='prefix',
                    help='Prefix to the view name, in fact is a name'
                    'of a module containing views to profile'),
        make_option('--profilers', dest='profilers', default='cProfiler',
                    help='List of the profilers to use: %s' %
                    PROFILERS.keys()),
        make_option('--limit', dest='limit', default=PROFILER_LIMIT,
                    help='Number of lines limit profiler stats output to.'
                    'Positive integer.'),
        make_option('--output', dest='output',
                    help='Outut filename'),
        )

    def handle(self, *args, **options):
        """Profile views with cProfile or LineProfiler or both."""

        verbosity = int(options.get('verbosity', 1))

        if verbosity:
            print 'Profiling....'

        prefix = options.get('prefix', None)
        output = options.get('output', None)
        profilers = options.get('profilers').split(',')
        limit = options.get('limit')
        try:
            limit = int(limit)
            if limit < 1:
                raise ValueError
        except TypeError, ValueError:
            print 'Wrong value for limit: %s\nMust be positive integer' % limit
            return

        if verbosity:
            print 'Using: %s' % profilers

        if args:
            view_names = [arg.split(':') for arg in args]
            try:
                views_module = __import__(prefix, {}, {}, [''])
            # TODO: specify exception
            except:
                print 'Cannot import module: %s' % prefix

        else:
            print 'No view names to profile, specify at least one'
            return

        # User is needed to be attached to get_request
        user_model = getattr(settings, 'PROFILER_USER_MODEL', None)

        try:
            # Import module containing user model
            user_model_name = user_model.split('.')[-1]
            user_module_name = '.'.join(user_model.split('.')[:-1])
            user_module = __import__(user_module_name, {}, {}, [''])
            user_model = getattr(user_module, user_model_name)
        except Exception, e:
            print 'Wrong PROFILER_USER_MODEL format: %s' % user_model
            print e
            return

        # Get user for the request
        user = user_model.objects.filter(is_superuser=True)[0]

        # Loop view names and profile views response rendering
        for view_name in view_names:
            # First element of ``view_name`` is the view name itself,
            # second element is a list of view function args separated by comma
            view_name, view_args = (view_name[0], view_name[1].split(',')) \
                if len(view_name) > 1 else (view_name[0], [])
            try:
                url = reverse(view_name, args=view_args)
            except NoReverseMatch, e:
                print e
                answer = raw_input('Try to perform '
                                   'as with function that asscepts'
                                   '``request`` as argument and returns'
                                   '``response`` object? (Y/N) ')
                if answer.lower() == 'y':
                    url = 'simulated-view-function'
                else:
                    print 'Excecution aborted'
                    return

            # Patch view to enable profiling
            view_function = getattr(views_module, view_name)

            # Construct GET request, attach user to it
            rf = client.RequestFactory()
            get_request = rf.get(url)
            get_request.user = user
            # Render response with profiling
            for profiler in profilers:
                response = profile(view_function,
                                   args=[get_request] + view_args,
                                   profiler=profiler,
                                   log_file=output,
                                   limit=limit)
                print '[OK] Profiled ``%s.%s``, response status code: %s\n' % \
                    (prefix, view_name, response.status_code)

                # Clean db queries list
                connection.queries = []

            # Print SQL queries
            full_args = [get_request] + view_args
            response = view_function(*full_args)
            sqlprinting_middleware = SqlPrintingMiddleware()
            sqlprinting_middleware.process_response({}, response)

            # Clean db queries list
            connection.queries = []
