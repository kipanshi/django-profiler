from django.db import connection
from django.conf import settings
import os


QUERIES_LIMIT = getattr(settings, 'PROFILER_QUERIES_LIMIT', 3)


def terminal_width():
    """
    Function to compute the terminal width.
    WARNING: This is not my code, but I've been using it forever and
    I don't remember where it came from.
    """
    width = 0
    try:
        import struct
        import fcntl
        import termios
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
        width = struct.unpack('HHHH', x)[1]
    except:
        pass
    if width <= 0:
        try:
            width = int(os.environ['COLUMNS'])
        except:
            pass
    if width <= 0:
        width = 80
    return width


class SqlPrintingMiddleware(object):
    """
    Middleware which prints out a list of all SQL queries done
    for each view that is processed.  This is only useful for debugging.
    Queries are sorted by time in descending order.
    Use ``SQLPRINTING_QUERIES_LIMIT`` setting to limit ouput to desired
    number of queries.
    """
    def process_response(self, request, response):
        indentation = 2
        if len(connection.queries) > 0 and settings.DEBUG:
            width = terminal_width()
            total_time = 0.0
            for query in sorted(connection.queries,
                                key=lambda query: query['time'],
                                reverse=True)[:QUERIES_LIMIT]:
                nice_sql = query['sql'].replace('"', '').replace(',', ', ')
                sql = "\033[1;31m[%s]\033[0m %s" % (query['time'], nice_sql)
                total_time = total_time + float(query['time'])
                while len(sql) > width - indentation:
                    print "%s%s" % (" " * indentation,
                                    sql[:width - indentation])
                    sql = sql[width - indentation:]
                print "%s%s\n" % (" " * indentation, sql)
            replace_tuple = (" " * indentation, str(total_time))
            print "%s\033[1;32m[EXECUTION TIME: %s seconds in %s of %s" \
                " queries]\033[0m" % (replace_tuple +
                                      (QUERIES_LIMIT,
                                           len(connection.queries)))
            print "%s\033[1;32m[TOTAL TIME: %s seconds in %s" \
                " queries]\033[0m" % (replace_tuple[0],
                                      sum([float(q['time'])
                                           for q in connection.queries]),
                                           len(connection.queries))
        return response
