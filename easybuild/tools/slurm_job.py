##
# Copyright 2012-2014 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
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
Interface module to SLURM.

@author: Jordi Blasco (NeSI)

Based on Interface module to TORQUE (PBS) developed by :
@author: Stijn De Weirdt (Ghent University)
@author: Toon Willems (Ghent University)
@author: Kenneth Hoste (Ghent University)
"""

import os
import os.path
import commands
import tempfile
import time
from vsc import fancylogger

_log = fancylogger.getLogger('slurm_job', fname=False)

# extend paramater should be 'NULL' in some functions because this is required by the python api
NULL = 'NULL'
# list of known hold types
KNOWN_HOLD_TYPES = []

class BatchJob(object):
    """Interaction with Slurm"""

    def __init__(self, script, name, env_vars=None, resources={}):
        """
        create a new Job to be submitted to Slurm
        env_vars is a dictionary with key-value pairs of environment variables that should be passed on to the job
        resources is a dictionary with optional keys: ['hours', 'cores'] both of these should be integer values.
        hours can be 1 - MAX_WALLTIME, cores depends on which cluster it is being run.
        """
        self.log = fancylogger.getLogger(self.__class__.__name__, fname=False)
        self.script = script
        if env_vars:
            self.env_vars = env_vars.copy()
        else:
            self.env_vars = {}
        self.name = name

        self.resources = {
                          "--job-name": "%s" % job_name,
                          "--time": "%s:00:00" % hours,
                          "--partition": "%s" % partition,
                          "--ntasks-per-node": "%s" % cores,
                          "--workdir": "%s" % workdir,
                          "--mail-user": "%s" % mail_user,
                          "--mail-type": "%s" % mail_type,
                          "-C": "%s" % architecture,
                          "--mem-per-cpu": "%s" % mem_per_cpu
                         }
        # job id of this job
        self.jobid = None
        # list of dependencies for this job
        self.deps = []
        # list of holds that are placed on this job
        self.holds = []

    def add_dependencies(self, job_ids):
        """
        Add dependencies to this job.
        job_ids is an array of job ids (e.g.: 8453....)
        if only one job_id is provided this function will also work
        """
        if isinstance(job_ids, str):
            job_ids = list(job_ids)

        self.deps.extend(job_ids)

    def submit(self, with_hold=False):
        """Submit the jobscript txt, set self.jobid"""

        # set resource requirements
        slurm_attributes.extend(self.resources)

        # add job dependencies to attributes
        if self.deps:
            deps_attributes[0].name = dependency
            deps_attributes[0].value = ",".join(["afterok:%s" % dep for dep in self.deps])
            slurm_attributes.extend(deps_attributes)
            self.log.debug("Job deps attributes: %s" % deps_attributes[0].value)

        # job submission sometimes fails without producing an error, e.g. when one of the dependency jobs has already finished
        # when that occurs, None will be returned by slurm_submit as job id
        jobdesc = (slurm_attributes, build_command);
        jobid = commands.getoutput('sbatch %s --wrap="%s" | awk \'{print $4}\'' % jobdesc);
        #is_error, errormsg = slurm.error()
        #if is_error or jobid is None:
        #    self.log.error("Failed to submit job script %s (job id: %s, error %s)" % (scriptfn, jobid, errormsg))
        #else:
        #    self.log.debug("Succesful job submission returned jobid %s" % jobid)
        #    self.jobid = jobid
        self.jobid = jobid

    def info(self, types=None):
        """
        Return jobinfo
        """
        if not self.jobid:
            self.log.debug("no jobid, job is not submitted yet?")
            return None

        # convert single type into list
        if type(types) is str:
            types = [types]

        self.log.debug("Return info types %s" % types)

        # create attribute list to query slurm.with
        if types is None:
            jobattr = NULL
        else:
            jobattr = slurm.new_attrl(len(types))
            for idx, attr in enumerate(types):
                jobattr[idx].name = attr

        # only expect to have a list with one element
        j = jobs[0]
        # convert attribs into useable dict
        job_details = dict([ (attrib.name, attrib.value) for attrib in j.attribs ])
        # manually set 'id' attribute
        job_details['id'] = j.name
        self.log.debug("Found jobinfo %s" % job_details)
        return job_details

