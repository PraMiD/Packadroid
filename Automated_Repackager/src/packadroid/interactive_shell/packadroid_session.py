import shutil
import os

from packadroid.apkhandling.packer import decompile_apk, repack_apk

class PackadroidSession():
    def __init__(self):
        self.__original_apk_path = None
        self.__original_apk_dec_path = None
        self.__hooks = []

    def get_hooks(self):
        return self.__hooks

    def load_original_apk(self, apk_path):
        if not os.path.isfile(apk_path):
            print("No .apk file found at the given path!")
            return

        self.__original_apk_dec_path = decompile_apk(apk_path)
        if self.__original_apk_dec_path is None:
            print("Could not decompile the original .apk file!")
            return

        self.__original_apk_path = apk_path
        print("Decompiled {} to {}".format(apk_path, self.__original_apk_dec_path))

    def add_hook(self, hook):
        self.__hooks.append(hook)

    def cleanup(self):
        if self.__original_apk_dec_path != None:
            print("Removing the decompiled original apk!")
            shutil.rmtree(self.__original_apk_dec_path)

