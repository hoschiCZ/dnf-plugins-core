# eol.py
# DNF plugin to check for EOL status of your distribution.
#
# Copyright (C) 2013-2017  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.

try:
    import urllib.request as urllib2  # for Python 3
except ImportError:
    import urllib2  # for Python 2
import dnf.cli
import logging
import os
import json
from dnf.i18n import _

logger = logging.getLogger('dnf')


class Eol(dnf.Plugin):
    """DNF plugin supplying the eol command."""

    name = 'eol'

    def sack(self):
        if next(self.base.repos.iter_enabled()).metadata._age < 100:
            # > metadata have just been updated.
            if get_eol_status(self.cli.base.conf.eolurl):
                logger.warning("\033[1m" +
                               "This version of your system has reached its End of Life! " +
                               "You are not receiving any new updates." +
                               "\033[0m")

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(Eol, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if cli is not None:
            cli.register_command(EolCommand)
    
    def config(self):
        cp = self.read_config(self.base.conf)
        self.base.conf.eolurl = cp.get('main', 'eol_url')


class EolCommand(dnf.cli.commands.Command):

    aliases = ('eol',)
    summary = _('get the lifecycle stage of your system')

    def __init__(self, cli):
        dnf.cli.commands.Command.__init__(self, cli)

    def run(self):
        logger.info(_("Lifecycle stage of your system: %s"),
                    "EOL" if get_eol_status(self.cli.base.conf.eolurl) else "Active")


def get_version_id():
    with open('/etc/os-release') as fp:
        for line in fp:
            if line.startswith("VERSION_ID="):
                return int(line.split("VERSION_ID=")[1])


def fetch_eol_status(versionid, apiurl):
    """Get EOL status of given version ID from a given PDC API.
    Returns true if the system has reached EOL, false if not yet."""

    rawresponse = urllib2.urlopen(apiurl + "?active=true&version=" + str(versionid)).read()
    try:  # required to support both Python 2 and 3
        response = json.loads(rawresponse.decode('utf-8'))
    except TypeError:
        response = json.loads(rawresponse)

    return (int(response["count"]) == 0)


def get_eol_status(apiurl):
    """Get EOL status of current system.
    apiurl -- PDC API URL from where to GET lifecycle information.
        Example: https://pdc.fedoraproject.org/rest_api/v1/releases/

    Returns true if system is at EOL, false otherwise."""

    versionid = get_version_id()
    return fetch_eol_status(versionid, apiurl)
