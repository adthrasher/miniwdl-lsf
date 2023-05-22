# Copyright (c) 2022- 
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import os
import shlex
import sys
import tempfile

from contextlib import ExitStack
from typing import Dict, List

from WDL import Type, Value
from WDL.runtime import config
from WDL.runtime.backend.cli_subprocess import _SubprocessScheduler
from WDL.runtime.backend.singularity import SingularityContainer
from WDL._util import StructuredLogMessage as _


class LSFSingularity(SingularityContainer):
    @classmethod
    def global_init(cls, cfg: config.Loader, logger: logging.Logger) -> None:
        # Set resources to maxsize. The base class (_SubProcessScheduler)
        # looks at the resources of the current host, but since we are
        # dealing with a cluster these limits do not apply.
        cls._resource_limits = {
            "cpu": sys.maxsize,
            "mem_bytes": sys.maxsize,
            "time": sys.maxsize,
        }
        _SubprocessScheduler.global_init(cls._resource_limits)
        # Since we run on the cluster, the images need to be placed in a
        # shared directory. The singularity cache itself cannot be shared
        # across nodes, as it can become corrupted when nodes pull the same
        # image. The solution is to pull image to a shared directory on the
        # submit node. If no image_cache is given, simply place a folder in
        # the current working directory.
        if cfg.get("singularity", "image_cache") == "":
            cfg.override(
                {"singularity": {
                    "image_cache": os.path.join(os.getcwd(),
                                                "miniwdl_singularity_cache")
                }}
            )
        SingularityContainer.global_init(cfg, logger)

    @classmethod
    def detect_resource_limits(cls, cfg: config.Loader,
                               logger: logging.Logger) -> Dict[str, int]:
        return cls._resource_limits  # type: ignore

    @property
    def cli_name(self) -> str:
        return "lsf_singularity"

    def process_runtime(self,
                        logger: logging.Logger,
                        runtime_eval: Dict[str, Value.Base]) -> None:
        """Any non-default runtime variables can be parsed here"""
        super().process_runtime(logger, runtime_eval)
        if "time_minutes" in runtime_eval:
            time_minutes = runtime_eval["time_minutes"].coerce(Type.Int()).value
            self.runtime_values["time_minutes"] = time_minutes

    def _lsf_invocation(self):
        # We use bsub -I as this makes the submitted job behave like a local job.
        bsub_args = [
            "bsub",
            "-K",
            "-J", self.run_id,
        ]

        # Redirect LSF logs to files
        bsub_args.extend(["-o", os.path.join(self.host_dir, f"stdout{self.try_counter if self.try_counter > 1 else ''}.lsf")])
        bsub_args.extend(["-e", os.path.join(self.host_dir, f"stderr{self.try_counter if self.try_counter > 1 else ''}.lsf")])

        cpu = self.runtime_values.get("cpu", None)
        if cpu is not None:
            bsub_args.extend(["-n", str(cpu)])
            bsub_args.extend(["-R span[hosts=1]"])

        # Get memory reservation for job in bytes
        memory = self.runtime_values.get("memory_reservation", 0)
        if memory is not None:
            # LSF memory specifications are per-core.
            # WDL (bioinformatics) tasks often specify memory per job.
            # This option divides the memory by the number of cores
            # prior to submission to LSF.
            memory_divisor = 1
            if self.cfg["lsf"].get_bool("memory_per_job") and cpu is not None:
               memory_divisor = cpu
            
            # Round to the nearest megabyte.
            bsub_args.extend(["-M", f"{round((memory / (1000 ** 2)) / memory_divisor)}M"])

        if self.cfg.has_section("lsf"):
            extra_args = self.cfg.get("lsf", "extra_args")
            if extra_args is not None:
                bsub_args.extend(shlex.split(extra_args))
        return bsub_args

    def _run_invocation(self, logger: logging.Logger, cleanup: ExitStack,
                        image: str) -> List[str]:
        singularity_command = super()._run_invocation(logger, cleanup, image)

        lsf_invocation = self._lsf_invocation()
        lsf_invocation.extend(singularity_command)
        logger.info("LSF invocation: " + ' '.join(
            shlex.quote(part) for part in lsf_invocation))
        return lsf_invocation
