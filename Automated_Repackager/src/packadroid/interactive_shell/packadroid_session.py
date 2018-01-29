import shutil
import os

from packadroid.apkhandling import packer
from packadroid.hookmanager import activity_hook
from packadroid.hookmanager import broadcast_hook

class PackadroidSession():
    def __init__(self):
        self.__original_apk_path = None
        self.__original_apk_dec_path = None
        self.__hooks = []

    def get_hooks(self):
        return self.__hooks

    def is_original_apk_loaded(self):
        return self.__original_apk_path != None

    def load_original_apk(self, apk_path):
        if not os.path.isfile(apk_path):
            print("No .apk file found at the given path!")
            return None

        self.__original_apk_dec_path = packer.decompile_apk(apk_path)
        if self.__original_apk_dec_path is None:
            print("Could not decompile the original .apk file!")
            return None

        self.__original_apk_path = apk_path
        print("Decompiled {} to {}".format(apk_path, self.__original_apk_dec_path))
        return self.__original_apk_dec_path

    def add_hook(self, hook):
        self.__hooks.append(hook)

    def repack(self, output=None):
        if not self.is_original_apk_loaded():
            print("No original .apk file loaded. Use load_original!")
            return None
        if len(self.get_hooks()) < 1:
            print("No hooks added. Nothing to repack!")
            return None

        activity_hooks = [h for h in self.get_hooks() if h.get_type() == "activity"]
        broadcast_hooks = [h for h in self.get_hooks() if h.type == "broadcast_receiver"]

        print("Inserting activity hooks.")
        activity_hook.inject_activity_hooks(self.__original_apk_dec_path, activity_hooks)

        print("Inserting broadcast receiver hooks.")
        broadcast_hook.inject_broadcast_receiver_hooks(self.__original_apk_dec_path, broadcast_hooks)

        if output == None:
            output = os.path.splitext(self.__original_apk_path)[0] +  "_repacked.apk"
        print("Repack apk as {}".format(output))
        packer.repack_apk(self.__original_apk_dec_path, self.__hooks, output)

        return output

    def cleanup(self):
        if self.__original_apk_dec_path != None:
            print("Removing the decompiled original apk!")
            shutil.rmtree(self.__original_apk_dec_path)

