import cProfile
import line_profiler
import os
import time
import hotshot
import hotshot.stats
import pstats

import settings

PROFILE_LOG_BASE = getattr(settings, 'PROFILE_LOG_BASE', '/tmp')
PROFILE_PROFILER = getattr(settings, 'PROFILE_PROFILER', 'LineProfiler')

try:
    from gprof2dot import PstatsParser, Profile
except ImportError:
    PstatsParser = object


class HotshotParser(PstatsParser):
    def __init__(self, filename):
        self.stats = hotshot.stats.load(filename)
        self.profile = Profile()
        self.function_ids = {}


class HotshotProfiler(object):
    def profile(self, outfile, func, *func_args, **func_kwargs):
        p = hotshot.Profile(outfile)
        result = p.runcall(func, *func_args, **func_kwargs)
        p.close()
        return result


class CProfileProfiler(object):
    def profile(self, outfile, func, *func_args, **func_kwargs):
        p = cProfile.Profile()
        result = p.runcall(func, *func_args, **func_kwargs)
        p.dump_stats(outfile)
        return result


class LineProfiler(object):
    def profile(self, outfile, func, *func_args, **func_kwargs):
        p = line_profiler.LineProfiler(func)
        result = p.runcall(func, *func_args, **func_kwargs)
        p.dump_stats(outfile)
        return result


# Supported profilers
PROFILERS = {
    'hotshot': HotshotProfiler(),
    'cProfile': CProfileProfiler(),
    'LineProfiler': LineProfiler(),
    }


def profile(log_file):
    """Profile some callable.

    This decorator uses the ``profiler`` to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
    file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof',
    where the time stamp is in UTC. This makes it easy to run and compare
    multiple trials.
    """

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y-%m-%d_%H-%M-%S",
                                              time.gmtime())
            final_log_file = base + ext

            profiler = PROFILERS[PROFILE_PROFILER]
            return profiler.profile(final_log_file, f, *args, **kwargs)

        return _inner
    return _outer
