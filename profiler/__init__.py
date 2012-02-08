import cProfile
import line_profiler

import settings

PROFILER_PROFILER = getattr(settings, 'PROFILE_PROFILER', 'LineProfiler')
PROFILER_LIMIT = getattr(settings, 'PROFILER_LIMIT', 30)


# TODO: Support for gprof2dot drawings
try:
    from gprof2dot import PstatsParser, Profile
except ImportError:
    PstatsParser = object


class CProfileProfiler(object):
    def profile(self, outfile, limit, func, *func_args, **func_kwargs):
        p = cProfile.Profile()
        result = p.runcall(func, *func_args, **func_kwargs)
        if outfile:
            p.dump_stats(outfile)
        else:
            import pstats
            sort = 'cumulative'  # sorty by cumulative time
            pstats.Stats(p).strip_dirs().sort_stats(sort).print_stats(limit)
        return result


class LineProfiler(object):
    def profile(self, outfile, limit, func, *func_args, **func_kwargs):
        """Currently LineProfiler does not support line-by-line stats for
        decorated functions. One need to comment decorator in order to see
        stats.

        """
        is_decorated, func = _search_for_orig(func)
        p = line_profiler.LineProfiler(func)
        result = p.runcall(func, *func_args, **func_kwargs)
        if outfile:
            p.dump_stats(outfile)
        else:
            p.print_stats()

        # Message in case of decorated function
        if is_decorated:
            print 'The view function is decorated. Currently LineProfiler ' \
                  'cannot show you by-line stats for the base function, ' \
                  'so to get line-by-line stats you will need to comment ' \
                  'decorators for this view.'
        return result


# Supported profilers
PROFILERS = {
    'cProfile': CProfileProfiler(),
    'LineProfiler': LineProfiler(),
    }


def profile(func, args=[], kwargs={}, **options):
    """Profile some callable.
    Serves as a wrapper, outputs the output of a profiled function.

    INPUT:
              ``func``   - function to profile
              ``args``   - list of function arguments
              ``kwargs`` - dict of function keyword arguments

    Options:
              ``log_file`` - if specified, filename where to store
                             profile stats
              ``profiler`` - profiler to use for profiling

    """

    log_file = options.get('log_file', None)
    limit = options.get('limit', PROFILER_LIMIT)
    profiler = PROFILERS[options.get('profiler', 'LineProfiler')]

    return profiler.profile(log_file, limit,
                            func, *args, **kwargs)


def _search_for_orig(func):
    """Search for the original function that is decorated."""
    if not getattr(func, '__closure__', None):
        return False, func
    for obj in (c.cell_contents for c in func.__closure__):
        if getattr(obj, '__name__', None) == func.__name__:
            is_decorated = True
            if getattr(obj, '__closure__', None):
                dummy, obj = _search_for_orig(obj)
            return is_decorated, obj


def _profile_decorated_func(func, profiler):
    """Append list containing original function
    plus applied decorator functions to the ``LineProfiler``.
    Outputs tuple of base function that was decorated and
    ``LineProfiler`` instance.

    """
    if not getattr(func, '__closure__', None):
        profiler.add_function(func)
        print 'Added function: %s' % func.__name__
        return func, profiler

    for obj in (c.cell_contents for c in func.__closure__):
        if getattr(obj, '__name__', None) == func.__name__:
            if getattr(obj, '__closure__', None):
                profiler.add_function(func)
                print 'Added function: %s' % func.__name__
                obj, profiler = _profile_decorated_func(obj, profiler)

            profiler.add_function(func)
            print 'Added function: %s' % func.__name__
            return obj, profiler
