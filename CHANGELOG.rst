==========
Changelog
==========

.. Newest changes should be on top.

.. This document is user facing. Please word the changes in such a way
.. that users understand how the changes affect the new version.

version 0.2.0
----------------------------
+ Add support for runtime hint `lsf.time` to specify the time limit
  for the job in minutes. Passed to bsub with the `-W` option.

version 0.1.2
----------------------------
+ Update memory reservation to use "-R rusage[mem=...]" instead of "-M".
  To use "-M", set "memory_limit_multiplier" in configuration to a 
  positive value.
+ Support config option "memory_limit_multiplier" to set a hard limit
  on memory usage.

version 0.1.1
----------------------------
+ Update log location on retry
+ Correct memory calculation

version 0.1.0
----------------------------
Initial release with the following features:

+ Utilize miniwdl's singularity backend to create a singularity command that
  is then submitted using bsub.
+ Create a singularity image cache so singularity images are available on
  the cluster nodes.
+ Support for ``cpu`` and ``memory`` runtime attributes.
