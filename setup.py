#!/usr/bin/env python

from distutils.core import setup

setup(name='django-profiler',
      version='1.0',
      description='Tools for profiling Django views with cPython,'
          ' optionally with Hotshot or LineProfiler',
      author='Kirill Panshin',
      author_email='kipanshi@gmail.com',
      url='http://github.com/kipanshi/django-profiler/',
      packages=['profiler',
                'profiler.management', 'profiler.management.commands'],
     )
