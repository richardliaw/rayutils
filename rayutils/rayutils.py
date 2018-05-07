from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import click
import pipes
import json
import subprocess
import os
import sys

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

def load_config(yaml_file_name):
    config = yaml.load(open(yaml_file_name).read())
    validate_config(config)
    return fillout_defaults(config)


def get_provider(config):
    """Returns provider.

    Modifies config"""
    importer = NODE_PROVIDERS.get(config["provider"]["type"])
    if not importer:
        raise NotImplementedError("Unsupported provider {}".format(
            config["provider"]))

    bootstrap_config, provider_cls = importer()
    config = bootstrap_config(config)
    return provider_cls(config["provider"], config["cluster_name"])


def get_head_updater(config):
    provider = get_provider(config)
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
    return NodeUpdaterProcess(
        head_node,
        config["provider"],
        config["auth"],
        config["cluster_name"],
        config["file_mounts"],
        [],
        runtime_hash,
        redirect_output=False)


@click.command()
def shutdown():
    """Executed on the headnode to terminate cluster"""
    subprocess.run(["ray", "stop"])
    with open(os.path.expanduser("~/ray_bootstrap_config.yaml")) as f:
        cfg = yaml.load(f)

    provider = get_provider(cfg)

    print("Terminating worker instances...")
    for instance_id in provider.nodes({"ray:NodeType": "Worker"}):
        provider.terminate_node(instance_id)

    print("Terminating head instance...")
    for instance_id in provider.nodes({"ray:NodeType": "Head"}):
        provider.terminate_node(instance_id)
    print("good bye!")



@click.command()
@click.argument("cluster_yaml", required=True, type=str)
@click.argument("cmd", required=True, type=str, nargs=-1)
def execute(cluster_yaml, cmd):
    """Executes command on cluster head."""
    config = load_config(cluster_yaml)
    head_updater = get_head_updater(config)
    head_updater.ssh_cmd(" ".join(cmd), verbose=True)


@click.command()
@click.argument("cluster_yaml", required=True, type=str)
def setup(cluster_yaml):
    """Makes sure utilities are installed on cluster head.

    Needed for shutdown."""
    config = load_config(cluster_yaml)
    head_updater = get_head_updater(config)
    git_path = "https://github.com/richardliaw/rayutils.git"
    gitclone = "git clone %s" % git_path
    install = "cd rayutils && pip install -e ."
    head_updater.ssh_cmd(gitclone, verbose=True)
    head_updater.ssh_cmd(install, verbose=True)


@click.command()
@click.argument("cluster_yaml", required=True, type=str)
def login_cmd(cluster_yaml):
    """Get login command for the head node"""
    from contextlib import redirect_stdout
    with redirect_stdout(open(os.devnull, 'w')):
        config = load_config(cluster_yaml)
        head_updater = get_head_updater(config)
    click.echo("ssh -i {key} {user}@{ip}".format(
        key=head_updater.ssh_private_key,
        user=head_updater.ssh_user,
        ip=head_updater.ssh_ip))



@click.command()
# TODO(rliaw: use CLICK primitive for reading file
@click.argument("cluster_yaml", required=True, type=str)
# TODO(rliaw): Restart ray on entire cluster
# @click.option("--restart-ray", is_flag=True, default=False,
#               help="Terminate cluster if job completes successfully")
@click.option("--shutdown", is_flag=True, default=False,
              help="Terminate cluster if job completes successfully")
@click.option("--background", is_flag=True, default=False,
              help="Runs job in a separate screen.")
@click.argument("script", required=True, type=str)
@click.argument("script_args", required=False, type=str, nargs=-1)
# TODO(rliaw): Terminate if job hangs for x minutes
def submit(cluster_yaml, shutdown, background, script, script_args):
    """Uploads and executes script on cluster"""
    # check that cluster is alive
    config = load_config(cluster_yaml)
    head_updater = get_head_updater(config)
    # check that cluster yaml is on head

    # syncs file to home directory on cluster
    base_script = os.path.basename(script)
    remote_dest = os.path.join("~", base_script)
    head_updater.sync_files({remote_dest: script})
    cmd_list = ["python", base_script] + list(script_args)
    if shutdown:
        cmd_list += ["&&", "ray2", "shutdown"]
    cmd = " ".join(cmd_list)
    if background:
        bg_cmd_list = ["screen", "-dm", "bash", "-c"] + [pipes.quote(cmd)]
        cmd = " ".join(bg_cmd_list)
    head_updater.ssh_cmd(cmd, verbose=True)
    # # executes script in a separate screen

    # head_updater.ssh_cmd(cmd, verbose=True)




cli.add_command(shutdown)
cli.add_command(execute)
cli.add_command(login_cmd)
cli.add_command(setup)
cli.add_command(submit)
