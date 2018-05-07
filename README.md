# Ray Utils

Mainly for autoscaling CLI. Will merge upstream if useful...
To install, run `pip install git+https://github.com/richardliaw/rayutils.git`.

## Use cases:
All commands currently need to insert cluster yaml in arg.
`$(ray2 login_cmd [cluster_yaml])` to log into head node

`ray2 setup` to install self-destruct capabilities on cluster

`ray2 execute [arbitrary] [cmd]` to run an arbitrary command

`ray2 shutdown` on cluster (only!) to self-destruct



Checkout `example/`.

