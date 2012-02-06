import cProfile
import line_profiler

import settings

PROFILER_PROFILER = getattr(settings, 'PROFILE_PROFILER', 'LineProfiler')
PROFILER_LIMIT = 50


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
        func1 = _search_for_orig(func)
        p = line_profiler.LineProfiler(func1)
        p.add_function(func)
        result = p.runcall(func1, *func_args, **func_kwargs)
        if outfile:
            p.dump_stats(outfile)
        else:
            p.print_stats()
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
        return func
    for obj in (c.cell_contents for c in func.__closure__):
        if getattr(obj, '__name__', None) == func.__name__:
            if getattr(obj, '__closure__', None):
                obj = _search_for_orig(obj)
            return obj


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
