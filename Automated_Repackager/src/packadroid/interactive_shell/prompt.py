import sys

from cmd import Cmd
from packadroid.interactive_shell.packadroid_session import PackadroidSession
from packadroid.hookmanager.hook import Hook

class PackadroidPrompt(Cmd):
    def start(self):
        self.prompt = '> '
        self.__setup_session()
        self.cmdloop("Started Packadroid Interactive Shell")

    def __setup_session(self):
        self.__packadroid_session = PackadroidSession()

    def do_load_original(self, args):
        """ Usage: load_original <path_to_original_apk> -- Load an .apk file you want inject code to. """
        args = args.split(" ")
        if len(args) != 1:
            print("You have to provide the path to an valid .apk file!")
            print(len(args))
            return
        self.__packadroid_session.load_original_apk(args[0])

    def do_exit(self, args):
        """ Usage: exit [-f] -- Close the interactive prompt without changing anything. """
        args = args.split(" ")
        if len(self.__packadroid_session.get_hooks())  < 1:
            self.exit(0)
        elif len(args) > 0 and args[0] is "-f":
            self.exit(0)
        print("If you really want to discard all changes and exit, add -f to the exit command!")

    def add_activity_hook(self, args):
        """ Usage: add_activity_hook <activity> <payload_path> <class> <method> -- Add a new hook to the given activity for the given payload. """
        args = args.split(" ")
        if len(args) < 4:
            print("Unknown format!")
            return
        self.__packadroid_session.add_hook(Hook("activity", args[0], args[2], args[3], args[1]))

    def exit(self, code):
        self.__packadroid_session.cleanup()
        sys.exit(code)
        