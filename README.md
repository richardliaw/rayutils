Desired work flow
    - Run autoscaler setup script
    -  upload experiment run script to machine
    -  run experiment on setup machine
    - Save experiment results on s3 when complete?
    - Kill machine when experiment is done/hangs

## Use cases:
`$(ray2 login_cmd [cluster_yaml])` to log into head node

`ray2 setup` to install self-destruct capabilities on cluster

`ray2 execute [arbitrary] [cmd]` to run an arbitrary command

`ray2 shutdown` on cluster (only!) to self-destruct
