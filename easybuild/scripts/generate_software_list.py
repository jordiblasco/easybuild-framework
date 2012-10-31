#!/usr/bin/env python
##
# Copyright 2012 Jens Timmerman
#
# This file is part of EasyBuild,
# originally created by the HPC team of the University of Ghent (http://ugent.be/hpc).
#
# http://github.com/hpcugent/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##

"""
This script will try to generate a list of supported software packages
by walking over a directory of easyconfig files and parsing them all

Sine this script will actually parse all easyconfigs and easyblocks
it will only produce a list of Packages that can actually be handled
correctly by easybuild.
"""
from datetime import date
from optparse import OptionParser
import os
import sys

from easybuild.framework.easyconfig import EasyConfig
from easybuild.framework import easyblock
from easybuild.tools.github import Githubfs
from vsc import fancylogger

# parse options
parser = OptionParser()
parser.add_option("-v", "--verbose", action="count", dest="verbose",
     help="Be more verbose, can be used multiple times.")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
     help="Don't be verbose, in fact, be quiet.")
parser.add_option("-b", "--branch", action="store", dest="branch",
     help="Choose the branch to link to (default develop).")
parser.add_option("-u", "--username", action="store", dest="username",
     help="Choose the user to link to (default hpcugent).")
parser.add_option("-r", "--repo", action="store", dest="repo",
     help="Choose the branch to link to (default easybuild-easyconfigs).")
parser.add_option("-p", "--path", action="store", dest="path",
     help="Specify a path inside the repo (default easybuild/easyconfigs).")

options, args = parser.parse_args()

# get and configure logger
log = fancylogger.getLogger(__name__)
if options.verbose == 1:
    fancylogger.setLogLevelWarning()
elif options.verbose == 2:
    fancylogger.setLogLevelInfo()
elif options.verbose >= 3:
    fancylogger.setLogLevelDebug()
if options.quiet:
    fancylogger.logToScreen(False)
if not options.username:
    options.username = "hpcugent"
if not options.repo:
    options.repo = "easybuild-easyconfigs"
if not options.path:
    options.path = "easybuild/easyconfigs"

log.info('parsing easyconfigs from user %s reponame %s' % (options.username, options.repo))

if not options.branch:
    options.branch = "develop"

configs = []
names = []

fs = Githubfs(options.username, options.repo, options.branch)

# fs.walk yields the same results as os.walk, so should be interchangable
# same for fs.join and os.path.join

for root, subfolders, files in fs.walk(options.path):    
    if '.git' in subfolders:
        log.info("found .git subfolder, ignoring it")
        subfolders.remove('.git')
    for file_ in files:
        file_ = fs.join(root,file_)
        file_ = fs.read(file_, api=False)
        try:
            
            ec = EasyConfig(file_, validate=False)
            log.info("found valid easyconfig %s" % ec) 
            if not ec.name in names:
                log.info("found new software package %s" % ec)
                # check if an easyblock exists
                module = easyblock.get_class(None, log, name=ec.name).__module__.split('.')[-1]
                if module != "configuremake":
                    ec.easyblock = module
                else:
                    ec.easyblock = None
                configs.append(ec)
                names.append(ec.name)
        except Exception, e:
            log.warning("faulty easyconfig %s" % file)
            log.debug(e)

log.info("Found easyconfigs: %s" % [x.name for x in configs])
# remove example configs
configs = [c for c in configs if not "example.com" in c['homepage']]
# sort by name
configs = sorted(configs, key=lambda config : config.name.lower())
firstl = ""

# print out the configs in markdown format for the wiki
print "Click on ![easyconfig logo](http://hpc.ugent.be/easybuild/images/easyblocks_configs_logo_16x16.png) " 
print "to see to the list of easyconfig files."
print "And on ![easyblock logo](http://hpc.ugent.be/easybuild/images/easyblocks_easyblocks_logo_16x16.png) "
print "to go to the easyblock for this package." 
print "## Supported Packages (%d in %s as of %s) " % (len(configs), options.branch, date.today().isoformat()) 
print "<center>"
print " - ".join(["[%(letter)s](#%(letter)s)" % \
    {'letter': x} for x in  sorted(set([config.name[0].upper() for config in configs]))])
print "</center>"

for config in configs: 
    if config.name[0].lower() != firstl:
        firstl = config.name[0].lower()
        # print the first letter and the number of packages starting with this letter we support
        print "\n### %(letter)s (%(count)d packages) <a name='%(letter)s'/>\n" % {
                'letter': firstl.upper(),
                'count': len([x for x in configs if x.name[0].lower() == firstl]),
            }
    print "* [![EasyConfigs](http://hpc.ugent.be/easybuild/images/easyblocks_configs_logo_16x16.png)] " 
    print "(https://github.com/hpcugent/easybuild-easyconfigs/tree/%s/easybuild/easyconfigs/%s/%s)" % \
            (options.branch, firstl, config.name)
    if config.easyblock:
        print "[![EasyBlocks](http://hpc.ugent.be/easybuild/images/easyblocks_easyblocks_logo_16x16.png)] "
        print " (https://github.com/hpcugent/easybuild-easyblocks/tree/%s/easybuild/easyblocks/%s/%s.py)" % \
            (options.branch, firstl, config.easyblock)
    else:
        print "&nbsp;&nbsp;&nbsp;&nbsp;"
    if config['homepage'] != "(none)":
        print "[ %s](%s)" % (config.name, config['homepage'])
    else:
        print config.name
