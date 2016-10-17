#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
import os


AUTHOR = u'Rodrigo Guzman'
SITENAME = u''
SITEURL = ''

PATH = 'content'

TIMEZONE = 'US/Eastern'

DFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None


# Blogroll
# LINKS = (('Pelican', 'http://getpelican.com/'),
#          ('Python.org', 'http://python.org/'),
#          ('Jinja2', 'http://jinja.pocoo.org/'),
#          ('You can modify those links in your config file', '#'),)

# Social widget
# SOCIAL = (('You can add links in your config file', '#'),
#          ('Another social link', '#'),)
DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

DEFAULT_DATE = 'fs'
DISPLAY_PAGES_ON_MENU = False
DISPLAY_CATEGORIES_ON_MENU = False

# theme and theme-specific settings
THEME = 'scratchpad-theme'
CSS_OVERRIDE = 'css/overrides.css'
COLOR_SCHEME_CSS = 'github_jekyll.css'
HEADER_COLOR = 'black'
HEADER_COVER = ''

ARTICLE_PATHS = ['articles']
PAGE_PATHS = ['pages']
STATIC_PATHS = ['images', 'css']

PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'


# override the footer
FOOTER_INCLUDE = 'custom_footer.html'
IGNORE_FILES = [FOOTER_INCLUDE]
EXTRA_TEMPLATES_PATHS = [os.path.join(os.path.dirname(__file__), 'templates')]
