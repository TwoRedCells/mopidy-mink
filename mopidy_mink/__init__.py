from __future__ import absolute_import, unicode_literals

import logging
import os

from mopidy import config, ext

__version__ = '0.1.0'


class Extension(ext.Extension):

    dist_name = 'Mopidy-Mink'
    ext_name = 'mink'
    version = __version__

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['playlist'] = config.String()
        schema['colour'] = config.String()
        return schema

    def get_default_config(self):
        return config.read(os.path.join(os.path.dirname(__file__), 'ext.conf'))

    def setup(self, registry):
        from .mink import Mink
        registry.add('frontend', Mink)
