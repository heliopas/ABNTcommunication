import binhex
import codecs
import socket
import csv
import time

import crcmod
import errno
from colorama import Fore, Back, Style
from time import sleep
import logging

host = "landis.iface" #Alias criado no arquivo c:\windows\system32\drivers\etc\hosts.file - 192.168.0.5 landis.iface
port = 33000
csvCMD = []

#logging config
logging.basicConfig(filename='../files/log.txt', format='%(asctime)s %(levelname)-8s %(message)s', level=logging.NOTSET)
logging.Formatter(fmt='%(asctime)s.%(msecs)03d', datefmt='%Y-%m-%d,%H:%M:%S')

def client_program(data):
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    while True:
        client_socket.send(bytes.fromhex(data))  # send message
        dararec = client_socket.recv(1024)  # receive response
        if dararec is None:
            dararec = client_socket.recv(1024)  # receive response
            print('Received from server: ' + dararec.hex())  # show in terminal
        else:
            print('Received from server: ' + dararec.hex())  # show in terminal
            break

    client_socket.close()  # close the connection

def loadCSV():
    global csvreader
    with open('../files/commands.csv', 'r') as file:
        csvreader = file.readlines()

def send(aux):
    try:
        client_socket.send(bytes.fromhex(aux))
    except socket.error as e:
        logging.error("Error during message send process: %s" % e)

def receive():
    try:
        return client_socket.recv(1024)  # receive response
    except socket.timeout as e:
        err = e.args[0]
        if err == 'timed out':
            logging.error("Connection time out to receive something!!!")

def closeCONN():
    try:
        client_socket.close()  # close the connection
    except socket.error as e:
        logging.error("Error during close connection: %s" % e.args[0])
    logging.info("      Port was closed!!!!")

def openCONN():
    global client_socket #socket configuration
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # instantiate

    try:
        client_socket.connect((host, port))  # connect to the server
    except socket.error as e:
        logging.error("Error during open connection: %s" % e.args[0])

    logging.info("Communication start sucess!#")
    client_socket.setblocking(False)
    client_socket.settimeout(10)

def islastFame(aux):
    if aux[14] == "1":
        return True
    else:
        return False

def calcCRC16(aux):
    crc16 = crcmod.mkCrcFun(poly=0x18005, initCrc=0xFFFF, xorOut=0x0000, rev=True)
    logging.info(f"CMD para calculo CRC: {aux}")
    crcvalueCalc = aux[0:516] # extrai frame para calculo de CRC
    logging.info(f"Frame para CRC calc: {crcvalueCalc}")
    crcvalueReceived = aux[-4:] # extrai CRC do frame
    logging.info(f"CRC: {crcvalueReceived}")

    calcChecksum = crc16(codecs.decode(crcvalueCalc, "hex")) # calcula CRC do fram
    logging.info(f"CRC calculado: {hex(calcChecksum)}")
    calcChecksum = hex(calcChecksum).removeprefix('0x') # remove 0x da String
    if len(calcChecksum) == 3:
        calcChecksum = '0'+calcChecksum
    if len(calcChecksum) == 2:
        calcChecksum = '00'+calcChecksum
    #print("CRC 0X:", calcChecksum)
    crcRotate = calcChecksum[2:4]+calcChecksum[0:2] # rotaciona CRC para check
    #print("CRC rotate:", crcRotate)
    if crcvalueReceived == crcRotate:
        logging.info(f"CRC OK")
        return True
    else:
        logging.error(f"CRC        NOK")
        return False

if __name__ == '__main__':
    while True:
        openCONN()
        # carrega comandos
        loadCSV()

        #envia commando 26
        send(csvreader[2].split(',')[1]) # send 26 cmd
        logging.info("Envia commando: %s" % csvreader[2].split(',')[0])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 26CMD again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 26CMD again")
                send(csvreader[2].split(',')[1])  # send 26 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[2].split(',')[1]).replace(' ','')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")

        while True:
            send(csvreader[3].split(',')[1]) # send 26 ack
            logging.info("Envia commando: %s" % csvreader[3].split(',')[0])
            try:
                aux = receive().hex()
                logging.info("Rec value Metter: %s" % aux)
            except AttributeError as e:
                err = e.args[0]
                logging.error(f"Nothing received from metter!!!->send 26 NAK")
                while aux is None:
                    logging.error(f"Nothing received from metter!!!->send 26 NAK")
                    send(csvreader[4].split(',')[1])  # send 26 NAK
                    aux = receive().hex()

            if calcCRC16(aux) is False:
                logging.error(f"    Erro de CRC!!!")

            if not ((csvreader[3].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
                logging.critical(f"Value received is wrong!!!!!")

            # else:
            #     print(Fore.GREEN, 'CRC OK!!!!')
            #print(Style.RESET_ALL) #volta cor fonte para default#
            #print(aux)

            if islastFame(aux) is True:
                send(csvreader[3].split(',')[1])  # send 26 ack
                logging.info("Last frame from : %s" % csvreader[3].split(',')[0])
                try:
                    aux = receive().hex()
                    logging.info("Rec value Metter: %s" % aux)
                except AttributeError as e:
                    err = e.args[0]
                    logging.error(f"Nothing received from metter!!!-> send 26 ACK last frame")
                    while aux is None:
                        logging.error(f"Nothing received from metter!!!-> send 26 ACK last frame")
                        send(csvreader[3].split(',')[1])  # send 26 ack
                        aux = receive().hex()

                if calcCRC16(aux) is False:
                    logging.error(f"    Erro de CRC!!!")

                if not ((csvreader[3].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
                    logging.critical(f"Value received is wrong!!!!!")

                # else:
                #     print(Fore.GREEN, 'CRC OK!!!!')
                #print(Style.RESET_ALL) #volta cor fonte para default#

                break

        #envia commando 51 canais 123

        send(csvreader[5].split(',')[1])  # send 51 cmd
        logging.info("Envia commando: %s" % csvreader[5].split(',')[1])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 51 ch1 cmd again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 51 ch1 cmd again")
                send(csvreader[5].split(',')[1])  # send 51 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[5].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")

        # envia commando 21 canal 123

        send(csvreader[6].split(',')[1])  # send 21 cmd
        logging.info("Envia commando: %s" % csvreader[6].split(',')[1])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 21 ch1 cmd again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 21 ch1 cmd again")
                send(csvreader[6].split(',')[1])  # send 21 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[6].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")

        #envia commando 26
        send(csvreader[2].split(',')[1]) # send 26 cmd
        logging.info("Envia commando: %s" % csvreader[2].split(',')[0])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 26CMD again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 26CMD again")
                send(csvreader[2].split(',')[1])  # send 26 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[2].split(',')[1]).replace(' ','')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")

        while True:
            send(csvreader[3].split(',')[1]) # send 26 ack
            logging.info("Envia commando: %s" % csvreader[3].split(',')[0])
            try:
                aux = receive().hex()
                logging.info("Rec value Metter: %s" % aux)
            except AttributeError as e:
                err = e.args[0]
                logging.error(f"Nothing received from metter!!!->send 26 NAK")
                while aux is None:
                    logging.error(f"Nothing received from metter!!!->send 26 NAK")
                    send(csvreader[4].split(',')[1])  # send 26 NAK
                    aux = receive().hex()

            if calcCRC16(aux) is False:
                logging.error(f"    Erro de CRC!!!")

            if not ((csvreader[3].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
                logging.critical(f"Value received is wrong!!!!!")

            # else:
            #     print(Fore.GREEN, 'CRC OK!!!!')
            #print(Style.RESET_ALL) #volta cor fonte para default#
            #print(aux)

            if islastFame(aux) is True:
                send(csvreader[3].split(',')[1])  # send 26 ack
                logging.info("Last frame from : %s" % csvreader[3].split(',')[0])
                try:
                    aux = receive().hex()
                    logging.info("Rec value Metter: %s" % aux)
                except AttributeError as e:
                    err = e.args[0]
                    logging.error(f"Nothing received from metter!!!-> send 26 ACK last frame")
                    while aux is None:
                        logging.error(f"Nothing received from metter!!!-> send 26 ACK last frame")
                        send(csvreader[3].split(',')[1])  # send 26 ack
                        aux = receive().hex()

                if calcCRC16(aux) is False:
                    logging.error(f"    Erro de CRC!!!")

                if not ((csvreader[3].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
                    logging.critical(f"Value received is wrong!!!!!")

                # else:
                #     print(Fore.GREEN, 'CRC OK!!!!')
                #print(Style.RESET_ALL) #volta cor fonte para default#

                break

        #envia commando 51 canais 456

        send(csvreader[7].split(',')[1])  # send 51 cmd
        logging.info("Envia commando: %s" % csvreader[7].split(',')[1])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 51 ch2 cmd again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 51 ch2 cmd again")
                send(csvreader[7].split(',')[1])  # send 51 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[7].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")


        # envia commando 21 canal 456

        send(csvreader[8].split(',')[1])  # send 21 cmd
        logging.info("Envia commando: %s" % csvreader[8].split(',')[1])
        try:
            aux = receive().hex()
            logging.info("Rec value Metter: %s" % aux)
        except AttributeError as e:
            err = e.args[0]
            logging.error(f"Nothing received from metter!!!->send 21 ch2 cmd again")
            while aux is None:
                logging.error(f"Nothing received from metter!!!->send 21 ch2 cmd again")
                send(csvreader[8].split(',')[1])  # send 21 cmd
                aux = receive().hex()

        if calcCRC16(aux) is False:
            logging.error(f"    Erro de CRC!!!")

        if not ((csvreader[8].split(',')[1]).replace(' ', '')[0:6]) == (aux[0:6]):
            logging.critical(f"Value received is wrong!!!!!")


        logging.info("                   Next interation@@@@@")

        closeCONN()