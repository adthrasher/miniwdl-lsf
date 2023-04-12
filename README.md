miniwdl-lsf
=============
Extends miniwdl to run workflows on LSF clusters in singularity containers.

This [LSF backend](https://miniwdl.readthedocs.io/en/latest/runner_backends.html) plugin for
[miniwdl](https://github.com/chanzuckerberg/miniwdl) runs WDL task containers
by creating a job script that is submitted to a LSF cluster. In case the job
description has a container, singularity will be used as container runtime.

Installation
------------
For the development version::

    pip install git+https://github.com/adthrasher/miniwdl-lsf.git

Configuration
--------------
The following [miniwdl configuration](https://miniwdl.readthedocs.io/en/latest/runner_reference.html#configuration)
example can be used to use miniwdl on a LSF cluster:

```
    [scheduler]
    container_backend=lsf_singularity
    # Sets the maximum concurrent tasks. Since LSF handles scheduling, we only
    # limit to avoid excessive overhead in miniwdl.
    task_concurrency=200
    
    # This setting allows running tasks to continue, even if one other tasks fails. 
    # Useful in combination with call caching. Prevents wasting resources by
    # cancelling jobs half-way that would probably succeed.
    fail_fast = false

    [call_cache]
    # The following settings create a call cache under the current directory.
    # This prevents wasting unnecessary resources on the cluster by rerunning 
    # jobs that have already succeeded.
    put = true 
    get = true 
    dir = "$PWD/miniwdl_call_cache"

    [task_runtime]
    # Setting a 'maxRetries' default allows jobs that fail due to intermittent
    # errors on the cluster to be retried.
    defaults = {
            "maxRetries": 2,
            "docker": "ubuntu:20.04"
        }

    command_shell = /bin/bash
 
    [singularity]
    # This plugin wraps the singularity backend. Make sure the settings are
    # appropriate for your cluster.
    exe = ["singularity"]

    # the miniwdl default options contain options to run as a fake root, which
    # is not available on most clusters.
    run_options = [
            "--containall",
            "--cleanenv"
        ]

    # Location of the singularity images (optional). The miniwdl-lsf plugin
    # will set it to a directory inside $PWD. This location must be reachable
    # for the submit nodes.
    image_cache = "$PWD/miniwdl_singularity_cache"

    [lsf]
    # extra arguments passed to the bsub command (optional).
    extra_args=""
    # Task memory specifications should be interpreted as per-job not per-core (LSF default)
    memory_per_job = true
```