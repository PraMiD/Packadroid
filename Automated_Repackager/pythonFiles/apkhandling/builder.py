import os

def decompileApk(apkPath):
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

def repackApk(decompiledPath):
    """
    Build/Repack the decompiled application given as parameter.
    The function will throw an :class:'Exception' on any error.

    :param decompiledPath: The path to the directory to the decompiled application.
    :type decompiledPath: str

    :return The path to the repacked .apk file.
    """
    if not os.path.isdir(decompiledPath):
        raise Exception("Cannot find the decompiled apk at path {}".format(decompiledPath))
    repackedApk = os.path.join(decompiledPath.replace("_decompiled", ""), ".apk")
    os.system("apktool b -o {} {}".format(decompiledPath, repackedApk))
    return repackedApk