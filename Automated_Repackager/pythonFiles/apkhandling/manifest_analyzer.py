import xml.etree.ElementTree as ET


def get_activity_name(activity):
    """returns name of xml encoded activity. (name may be dirty with android tags)"""
    for key in activity.attrib.keys():
        if key.endswith("name"):
            return activity.attrib[key]


def find_launcher_activity(manifest_path):
    """
        Finds the launcher activity (or multiple) from xml.etree.ElementTree.
        Given: Manifest Path
    """
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    package = root.attrib['package']

    application = [child for child in root if child.tag == 'application']
    activities = [x for x in application[0] if x.tag == 'activity']

    activities_with_intent_filter = []

    for activity in activities:
        # print activity
        intent_filters = [x for x in activity if x.tag == 'intent-filter']
        for intent_filter in intent_filters:
            #for action in [x for x in intent_filter if x.tag == 'action']:
                #if ('{http://schemas.android.com/apk/res/android}name' in action.attrib
                    #and action.attrib['{http://schemas.android.com/apk/res/android}name'] == "android.intent.action.MAIN"):
                    #activities_with_intent_filter.append(get_activity_name(activity))

            if intent_filter.attrib != {}:
                for category in intent_filter:
                    if category.tag == 'category':
                        if ('{http://schemas.android.com/apk/res/android}name' in category.attrib
                            and category.attrib['{http://schemas.android.com/apk/res/android}name'] == "android.intent.category.LAUNCHER"):
                            activities_with_intent_filter.append(get_activity_name(activity))
    return list(set(activities_with_intent_filter))


def get_permissions(manifest_path):
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    permissions = [x for x in root if "permission" in x.tag]

    permissions = [x.attrib["{http://schemas.android.com/apk/res/android}name"] for x in permissions]

    return list(set(permissions))


def add_permissions_to_manifest(original_manifest_path, output_manifest_path, novel_permissions):
    """
        Add additional permissions to the manifest.
        This method ensures that no permissions are duplicated within the resulting manifest.

        :param original_manifest_path: Path of the original manifest file
        :param output_manifest_path: Path where the modified manifest is exported to
        :param novel_permissions: List(!) of permissions, given as strings
    """
    original_permissions = get_permissions(original_manifest_path)

    add_permissions = [x for x in novel_permissions if x not in original_permissions]

    manifest_lines = []
    with open(original_manifest_path) as f:
        manifest_lines.extend(f.read().splitlines())

    inject = 0
    novel_manifest = []
    for line in manifest_lines:
        if "uses-permission" in line and inject == 0:
            for permission in add_permissions:
                print permission
                novel_manifest.append("    <uses-permission android:name=\"" + permission + "\" />")
            novel_manifest.append(line)
            inject = 1
        else:
            novel_manifest.append(line)

    export_data(novel_manifest, output_manifest_path)


def add_receiver(manifest_path, receiver):
    """
    Adds the given receiver to the manifest on the given path inside of the application bound (<application>...</application>)

    :param manifest_path: Path of the manifest file
    :type manifest_path: str
    :param receiver: The Broadcast receiver which has to be added
    :type receiver: str

    :return
    pass
    """

    manifest_lines = []
    with open(manifest_path) as f:
        manifest_lines.extend(f.read().splitlines())
    
    novel_manifest = []
    inserted = False
    for line in manifest_lines:
        novel_manifest.append(line)
        if "<application" in line and not inserted:
            novel_manifest.append(receiver)
            inserted = True

    export_data(novel_manifest, manifest_path)

def export_data(data, out_path):    
    """
        Exports a list of data items to a given output path.
        Each item is stored in a seperate line.
        :param data: List of data items
        :param out_path: Path to store the data
    """
    with open(out_path, "w") as f:
        for item in data:
            if item != "\n":
                f.write(item + "\n")
            else:
                f.write(item)



def fix_manifest(payload_manifest_path, original_manifest_path,
                 output_manifest_path):
    """
        Fix manifest located at the provided manifest path.
        TODO: provide list of additional permissions to be added
        :param manifest_path:
        :return:
    """
    payload_permissions = get_permissions(payload_manifest_path)

    add_permissions_to_manifest(original_manifest_path, output_manifest_path, payload_permissions);



if __name__ == "__main__":
    x = find_launcher_activity('../AndroidManifest.xml')
    print(y)
