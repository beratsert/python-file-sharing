import socket
import os
from _thread import *
import threading
import time
import sys
import datetime

# Credentials
PORT=12345
HOST=''
packetonAir = 0
SendThreads = list()
packetsendSize = 0
Ipandnames = dict()
AcknowledgedPacketNum = 0


def clear():
    os.system('clear')

# Gets the IP of user
def get_ip():
    clear()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        global HOST
        s.connect(('10.255.255.255', 1))
        HOST = s.getsockname()[0]
    except:
        HOST = '127.0.0.1'
    finally:
        clear()
        print("\n\nWelcome to Social Torrent!\n")
        print("Your IP : %s\n" % (HOST))
        s.close()
        enter_command()

def enter_command():
    input("\nPress Enter to continue...")
    main_menu()

# There you have to choose uploading or downloading
def main_menu():
    clear()
    print("\nSocial Torrent enables users to file transfer.\n")
    print("Type 1 to upload file.\n")
    print("Type 2 to download file.\n")
    print("\nYou can exit by typing 0")
    navigator()

def navigator():
    tmp=input("\n\nPlease type your selection..")
    if tmp == '1':
        uploader()
    elif tmp == '2':
        downloader()
    elif tmp == '0':
        clear()
        print("See you again!!")
        sys.exit(0)
    else:
        main_menu()

# lists available files to upload and due to requested file, uploads files as a thread
def uploader():
    clear()
    print("Available files in the current directory\n")
    Files=os.listdir('.')
    print(*Files, sep='\n')
    upload_thread = threading.Thread(target=upload)
    upload_thread.setDaemon(True)
    upload_thread.start()
    enter_command()

# Using TCP mechanism over UDP, sends the file frame by frame...
def upload():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.bind((HOST,12345))
        s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1000)
        file ,address = s.recvfrom(1024)
        file = file.decode("utf-8")
        if os.path.isfile(file):
            fileSize = os.path.getsize(file)
            s.sendto(f"{fileSize}".encode(),address)
            answer = s.recvfrom(1024)[0].decode("utf-8")
            ans = answer.split("+")
            rwnd = int(ans[1])
            if ans[0] == "OK":
                packets = list()
                with open(file, "rb") as binary_file:
                    i = 0
                    bytesToSend = binary_file.read(1496)
                    while bytesToSend != b'':
                        packets.append( (i).to_bytes(4, byteorder ="little", signed = True) + bytesToSend )
                        i = i+1
                        bytesToSend = binary_file.read(1496)

                    j = 0
                    Maximumpcktsonair = rwnd // 1500

                    while j < Maximumpcktsonair:
                        threading.Thread(target=sendPackets, args=(packets[j], address, j)).start()
                        if j < i - 1 :
                            j = j + 1
                        else:
                            break
                    print("Successfully Uploaded!")
                    global AcknowledgedPackets
                    AcknowledgedPackets = [-1] * i
                    global AcknowledgedPacketNum
                    AcknowledgedPacketNum = 0
                    global packetsendSize
                    a = threading.Thread(target=receivepackets, args=(s,))
                    while AcknowledgedPacketNum < i:

                            #s.settimeout(3)
                            if not a.is_alive():
                                a = threading.Thread(target=receivepackets, args=(s,))
                                a.start()


                            #print(f"There are {packetonAir} packets on air out of {Maximumpcktsonair} and  {packetsendSize} and i {i}")
                            if packetonAir < Maximumpcktsonair and packetsendSize > 0:
                                    threading.Thread(target=sendPackets, args=(packets[j], address, j)).start()
                                    if j < i - 1:
                                        j = j + 1

def sendPackets(packet,address,number):
    global packetonAir
    global AcknowledgedPackets
    isSent = False
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1000)
        while not isSent:
            s.sendto(packet, address)
            packetonAir = packetonAir + 1
            time.sleep(1)
            packetonAir = packetonAir - 1
            if number in AcknowledgedPackets:
                #print(f"{number}THREAD STOPPED {packetonAir}")
                isSent = True


def receivepackets(s):
    global packetsendSize
    global  AcknowledgedPacketNum
    global AcknowledgedPackets
    try:
        #print(AcknowledgedPackets)
        ack = s.recvfrom(1024)[0].decode("utf-8")
        #print(ack)
        acks = ack.split("+")
        packetsendSize = int(acks[1]) // 1500
        #print(acks[0])
        acknowledgednum = int(acks[0])
        if acknowledgednum not in AcknowledgedPackets:
            AcknowledgedPackets[acknowledgednum] = acknowledgednum
            AcknowledgedPacketNum = AcknowledgedPacketNum + 1
    except:
        pass

# Asks you the sender IP and the name of the desired file, then, asks to the uploader whether there is an existing
#file. Finally, by sending ACK, downloads frame by frame.

def downloader():
    clear()
    download_ip=input("\n\nPlease type uploader IP..\n")
    clear()
    print("Source IP:" + download_ip )
    print("\nLoading..")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, 1234))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,45000)

        while True:
            address = (download_ip, 12345)
            inp2 = input("\n\nPlease type the name of the file!(Hint: You can use example1.jpg, lyrics.txt..)\n")
            s.sendto(inp2.encode(), address)
            fileSize = s.recvfrom(1500)[0].decode("utf-8")
            numberofpackets = 1 + int(fileSize)//1496
            print("Size of the "+inp2+ " : " +fileSize)
            download = input("\nAre you sure? (Y/N)")
            packets = [b''] * numberofpackets
            packetsbool = [False] * numberofpackets
            if download == "Y":
                s.sendto("OK+45000".encode(), address)
                packetreceived = 0
                while False in packetsbool:
                    try:
                        file = s.recvfrom(1500)[0]
                        packetNum = int.from_bytes(file[0:4] , byteorder="little", signed=True)
                        packets[packetNum] = file[4:]
                        s.sendto(f"{packetNum}+45000".encode() ,address)
                        packetreceived = packetreceived + 1
                        packetsbool[packetNum] = True
                        #print(packetsbool)
                    except:
                        pass
                with open("new_" + inp2, 'a+b') as myFile:
                    for i in range(numberofpackets):
                        myFile.write(packets[i])
                    clear()
                    print("\n"+inp2+ " is downloaded as new_"+inp2+"!\n")
                    enter_command()
            else:
                downloader()

get_ip()
