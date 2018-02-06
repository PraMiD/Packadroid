Packadroid -- A Framework for Repackaging Android Applications
==============================================================

**Packadroid** is a framework that allows the automated repackaging *Android* applications.

Documentation
--------------

To get a full documentation of the project, please refer to the files contained in the *docs* directory of this repository.
This directory contains a report and slides that explain the approach we used, the project structure and the usage in more detail.


Directory structure
-------------------

In the following we shortly explain the directory structure of this repository:

* docs: Contains further documentation of the project.
* src: Contains the *Python* sources of the project.
* payload: Contains precompiled payloads in apk files. The available payloads are explained in the *Payload* section.
* payload_src: Contains the source code of the precompiled payloads as an *Android Studio* project.


Usage
------
The **Packadroid** frameworks supports the following commands.
To start the interactive shell, use:

    python repackager.py [-b <batch_file>]

The following table shows the supported commands.
The commands can be listed inside the interactive shell using the *help* command.

| Command | Usage | Explanation |
|---------------------------|-------|-------------|
| add_activity_hook         | add_activity_hook <activity name OR activity ID> <payload_apk_path> <class> <method> | Add a new hook to the given activity for the given payload. The activity IDs can be listed with list_activities.
| add_broadcast_hook        | add_broadcast_hook <broadcast> <payload_apk_path> <class> <method> | Add a new hook to the given intent as a broadcastreceiver. 
| exit                      | exit [-f] | Close the interactive prompt without changing anything. 
| generate_meterpreter      | generate_meterpreter <IP> <lport> | Generate a reverse shell (meterpreter) with given IP and port. Metasploit necessary!
| help                      | help - shows available methods without problems
| list_activities           | list_activities | List the activities of the loaded original application. [*] marks launcher activities. The number before each activity is its ID. This ID can be used in the add_activity_hook command.
| list_added_hooks          | list_added_hooks   | Lists all hooks which have already been added by the user. Each hook has an ID which can be used to remove hooks. 
| list_permissions          | list_permissions | List the permissions of the loaded original application.
| load_original             | load_original <path_to_original_apk> | Load an .apk file you want inject code to. 
| remove_hook               | remove_hook <index>  | Remove hook with given index. For retrieving the index of each hook use the list_added_hooks function.
| repack                    | repack [repacked_apk_path] | Repack the .apk file as configured!
| set_verbose               | set_verbose <value> | Enables (1) or disables (0) the verbose modewhich shows enriched shell output.
| start_meterpreter_handler | start_meterpreter_handler <IP> <lport> | Generate a handler which is catchign the reverse shell 
| unload_session            | unload_session | Deletes all settings of the current session. Deletes folder of decompiled apps/payloads.


For easier automation, it is possible to specify a batch file containing the commands to execute.
The batch file is a simple text file which contains commands you would usually enter directoy into the interactive shell.
The batchfile is executed using the following command:

    python repackager.py [-b <batch_file>]


Payloads
--------

We deliver the following precompiled payloads:

|         Class          |       Method      |         .apk file       | Explanation |
|------------------------|-------------------|-------------------------|-------------|
| com.tum.team05.packadroidpayload.Payload | deleteAllContacts | payload/precompiled.apk | Deletes all contacts when the hook is triggered. |
| com.tum.team05.packadroidpayload.Payload | startRecording    | payload/precompiled.apk | Starts recording using the microphone. The output is written to the *output.mp3* file in the standard working directory of the application. |
| com.tum.team05.packadroidpayload.Payload | sendSms           | payload/precompiled.apk | Sends an SMS to a dummy phone number and static content. Feel free to adapt the soruce code of the payload! |
| com.tum.team05.packadroidpayload.Payload | transferContacts  | payload/precompiled.apk | Transfer a list of all contact to a dummy EMail address. |

The provided precompiled payloads currently do not request runtime *Android* permissions.
Therefore, they do not work for *Android* versions greater thatn 6.0 (API level 23).
However, feel free to adapt the payloads.

In addition, to the precompiled payloads we support to build a *Meterpreter*-based reverse shell.
As you have to enter your own IP address and the port you want to use, we do not deliver a precompiled version of this payload!


Installation
------------

To install the framework you have to do the following steps:

* Download the repository.
* Install dependencies listed in the dependencies section.


Dependencies
------------

To execute the framework itself, you have to use *Python 3* on a Linux/Ubuntu-based system.
In addition, we require the following dependencies:

* There are currently no special *Python 3* dependencies.
* Make sure *apktool* is accessible from the command line (We used version 2.3.1 for testing).
* Make sure *jarsigner* is accessible from the command line. Jarsigner uses the *androiddebugkey* for testing.
Therefore, you also have to ensure that the *~/.android/debug.keystore* file contains a key called *androiddebugkey*. This key is usually installed as soon as *android-studio* is installed on the system.
* To generate and use the *Meterpreter* reverse shell, *Metasploit* must be installed on the system and *msfvenom* and *msfconsole* must be executable from the command line.