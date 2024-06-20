import socket

UDP_IP = "192.168.1.25"
# LOCAL_IP = "192.168.1.1"
UDP_PORT = 2000
MESSAGE = bytearray([255]*22)

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
# sock.bind((UDP_IP, UDP_PORT))

attemps = 5
while(attemps>0):
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

    # while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message: %s" % data)

    attemps-=1