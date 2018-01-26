import errno
import os

def hook_activities(hooks, original_apk):
    """
        Create the hooked smali.

        :param hooks: List of activity hooks we shall inject into the original apk
        :type hooks: [:class:'hookmanager.Hook']

        :param original_apk: Path to the decompiled original apk
        :type original_apk: str
    """

    print("Hooking the desired activities.")

    if not os.path.isdir(original_apk):
        print("Cannot find the decompiled original application at {}".format(original_apk))
        print("No activity hook is inserted!")
        return

    activities = {}
    for hook in hooks:
        location = hook.get_location()
        if location not in activities.keys():
            activities[location] = []
        activities[location].append(hook)

    for activity, hooks in activities.items():
        __inject_hook_call(original_apk, activity, hooks)


def __inject_hook_call(original_apk, activity, hooks):
    """
        Inject several hook calls to different methods in the same activity.

        :param original_apk: Path to the original decompiled application.
        :type original_apk: str

        :param activity: Name (including package name) of the activity we want to hook.
        :param activity: str

        :param hooks: The :class:'hookmanager.Hook' objects we want to insert at this location
        :type hooks: [:class:'hookmanager.Hook']
    """
    activity_smali = []
    smali_path = os.path.join(original_apk, "smali", activity.replace(".", "/"))

    if not os.path.isfile(smali_path):
        print("Cannot load smali file for activity {} at path {}!".format(activity, smali_path)
        return

    print("Hooking activity: {}".format(activity))
    hook_location = ';->onCreate(Landroid/os/Bundle;)V'
    with open(smali_path) as f:
        line = f.readline()

        activity_smali.append(line)
        if hook_location in line:
            for hook in hooks:
                c = hook.get_class().replace(".", "/")
                m = hook.get_method()
                call = "\n\tinvoke-static {p0}, L{};->{}(Landroid/content/Context;)V".format(c, m)
                activity_smali.append(call)

    print("Writing back activity: {}".format(activity))
    with open(smali_path, "w") as f:
        f.write("".join(activity_smali))

