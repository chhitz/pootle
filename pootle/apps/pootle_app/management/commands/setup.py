#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.db.utils import DatabaseError

from pootle_misc import siteconfig


class Command(NoArgsCommand):
    help = 'Runs the install/upgrade machinery.'

    def handle_noargs(self, **options):
        try:
            config = siteconfig.load_site_config()
            current_buildversion = config.get('POOTLE_BUILDVERSION', None)

            if current_buildversion is None:
                # Old Pootle versions used BUILDVERSION instead.
                current_buildversion = config.get('BUILDVERSION', None)
        except DatabaseError:
            # Assume that the DatabaseError is because we have a blank database
            # from a new install, is there a better way to do this?
            current_buildversion = None

        if current_buildversion is None:
            logging.info('Setting up a new Pootle installation.')

            call_command('syncdb', interactive=False)
            call_command('migrate')
            call_command('initdb')

            logging.info('Successfully deployed new Pootle.')
        else:
            logging.info('Upgrading existing Pootle installation.')

            call_command('updatedb')  # Only run if Pootle is < 2.5.0.
            call_command('syncdb', interactive=False)

            if current_buildversion < 25100:
                # We are upgrading from a pre-South installation (before Pootle
                # 2.5.1), so it is necessary to fake the first migration for
                # some apps.
                OLD_APPS = ("pootle_app", "pootle_language",
                            "pootle_notifications", "pootle_profile",
                            "pootle_project", "pootle_statistics",
                            "pootle_store", "pootle_translationproject",
                            "staticpages")
                for app in OLD_APPS:
                    call_command("migrate", app, "0001", fake=True)

            call_command('migrate')
            call_command('upgrade')

            logging.info('Successfully upgraded Pootle.')