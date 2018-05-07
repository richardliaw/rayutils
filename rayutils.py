from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import click
import json
import subprocess

import ray.services as services
from ray.autoscaler.commands import (create_or_update_cluster,
                                     teardown_cluster, get_head_node_ip)

from ray.autoscaler.autoscaler import validate_config, hash_runtime_conf, \
    hash_launch_conf, fillout_defaults
from ray.autoscaler.node_provider import get_node_provider, NODE_PROVIDERS
from ray.autoscaler.tags import TAG_RAY_NODE_TYPE, TAG_RAY_LAUNCH_CONFIG, \
    TAG_NAME
from ray.autoscaler.updater import NodeUpdaterProcess
import yaml


@click.group()
def cli():
    pass


@click.command()
@click.argument("cluster_config_file", required=True, type=str)
def sync(cluster_config_file):
    """Only syncs file mounts with entire cluster"""
    config = yaml.load(open(config_file).read())
    provider = get_node_provider(config["provider"], config["cluster_name"])
    head_node_tags = {
        TAG_RAY_NODE_TYPE: "Head",
    }
    nodes = provider.nodes(head_node_tags)
    if len(nodes) > 0:
        head_node = nodes[0]
    else:
        print("Head node of cluster ({}) not found!".format(
            config["cluster_name"]))
        sys.exit(1)

    runtime_hash = hash_runtime_conf(config["file_mounts"], config)

    updater = NodeUpdaterProcess(
        head_node,
        config["provider"],
        config["auth"],
        config["cluster_name"],
        config["file_mounts"],
        [],
        runtime_hash,
        redirect_output=False)
    updater.sync_files(config["file_mounts"])


@click.command()
def shutdown():
    """Executed on the headnode to terminate cluster"""
    raise NotImplementedError
    pass
    # stop ray
    pass
    # terminate workers
    pass
    # terminate head
    pass


def check_cluster(config):
    provider = get_node_provider(config["provider"], config["cluster_name"])
    head_node_tags = {
        TAG_RAY_NODE_TYPE: "Head",
    }
    nodes = provider.nodes(head_node_tags)
    return len(nodes) > 0


@click.command()
@click.argument("cluster_yaml", required=True, type=str)
def setup(cluster_yaml):
    """Executed on the headnode to terminate cluster"""
    config = yaml.load(open(config_file).read())
    assert is_cluster_up(config), "Cluster not alive!"

    head_updater = get_head_updater(config)
    head_updater.ssh_cmd(["pip", "install", verbose=True)





@click.command()
# TODO(rliaw: use CLICK primitive for reading file
@click.argument("cluster_yaml", required=True, type=str)
# TODO(rliaw): Restart ray on entire cluster
# @click.option("--restart-ray", is_flag=True, default=False,
#               help="Terminate cluster if job completes successfully")
@click.option("--shutdown", is_flag=True, default=False,
              help="Terminate cluster if job completes successfully")
@click.argument("script_args", required=True, type=str, nargs=-1)
# TODO(rliaw): Terminate if job hangs for x minutes
def submit(cluster_yaml, shutdown, script_args):
    """Uploads and executes script on cluster"""
    # check that cluster is alive
    config = yaml.load(open(config_file).read())
    assert is_cluster_up(config), "Cluster not alive!"

    head_updater = get_head_updater(config)
    # check that cluster yaml is on head

    # syncs file to home directory on cluster
    script = script_args[0]
    remote_dest = os.path.join("~", os.path.basename(script))
    updater.sync_files({remote_dest: script})

    # executes script in a separate screen
    # "screen", "-dm", ""
    cmds = ["python"] + list(script_args)
    # if shutdown, appends shutdown command to script
    if shutdown:
        cmd += ["&&"] + ["ray2", "shutdown", cluster_yaml_dir]
    head_updater.ssh_cmd(cmd, verbose=True)




cli.add_command(shutdown)
cli.add_command(submit)
