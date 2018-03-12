import argparse
import sys
import os

from packadroid.apkhandling import packer
from packadroid.manifestmanager import manifest_analyzer, manifest_changer
from packadroid.hookmanager import activity_hook, broadcast_hook
from packadroid.interactive_shell.prompt import PackadroidPrompt


def parseArgs():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-b", "--batch", action="store", dest="batch", default=None)
    args_parsed = parser.parse_args(sys.argv[1:])

    # convert to dictonary
    return vars(args_parsed)

args = parseArgs()
prompt = PackadroidPrompt()
if args['batch'] is not None:
    cmds = []
    batch_file = args['batch']
    if not os.path.isfile(batch_file):
        print("Cannot load batch file from location {}".format(batch_file))
        sys.exit(1)
    with open(batch_file, "r") as f:
        cmds = f.read().splitlines()
    try:
        # Execute the commands given in the batch file first!
        prompt.execute_commands(cmds)
    except Exception:
            prompt.get_session().cleanup()
            raise
prompt.start()
