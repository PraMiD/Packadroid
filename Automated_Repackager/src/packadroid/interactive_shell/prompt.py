import sys

from cmd import Cmd
from packadroid.interactive_shell.packadroid_session import PackadroidSession
from packadroid.hookmanager.hook import Hook

ERR = True
SUC = False

class PackadroidPrompt(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = '> '
        self.__setup_session()

    def start(self):
        self.cmdloop("Started Packadroid Interactive Shell")
        while True:
            # There might be errors while executing a command, but we want to keep the prompt open
            self.cmdloop("")

    def do_load_original(self, args):
        """ Usage: load_original <path_to_original_apk> -- Load an .apk file you want inject code to. """
        args = args.split(" ")
        if len(args) != 1:
            print("You have to provide the path to an valid .apk file!")
            print(len(args))
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

    def do_repack(self, args):
        """ Usage: repack [repacked_apk_path] -- Repack the .apk file as configured! """
        args = args.split(" ")
        if len(args) != 0:
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
        """ Usage: add_activity_hook <activity> <payload_apk_path> <class> <method> -- Add a new hook to the given activity for the given payload. """
        args = args.split(" ")
        if len(args) < 4:
            print("Unknown format!")
            return ERR
        self.__packadroid_session.add_hook("activity", args[0], args[2], args[3], args[1])
        return SUC

    def execute_commands(self, cmds):
        """
        Execute a list of commands given in a 'configuration' file.

        :param cmds: List of commands to execute.
        :type cmds: [str]
        """
        for cmd in cmds:
            if self.onecmd(cmd): # Stop -> An error happened in one of the commands!
                self.__exit(1)

    def __setup_session(self):
        self.__packadroid_session = PackadroidSession()

    def __exit(self, code):
        self.__packadroid_session.cleanup()
        sys.exit(code)