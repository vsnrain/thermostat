import sys
import usb.core
import usb.util
import struct
import time

VENDOR  = 0x0451
PRODUCT = 0xd00e

EP_BULK_IN  = 0x81
EP_BULK_OUT = 0x01
BUF_LEN     = 512

def read(length=BUF_LEN):
    data = b''
    try:
        data = dev.read(EP_BULK_IN, length, timeout=1000)
    except Exception as e:
        print(f'[-]   read: USB read exception: {e}')
        exit(1)

    #print(f'[+]   read: USB read OK, len: {len(data)}')
    return bytes(data)

def write(data):
    offset = 0
    written = 0
    while offset < len(data):
        chunk = data[offset:offset+BUF_LEN]
        try:
            written = dev.write(EP_BULK_OUT, chunk, timeout=1000)
            if written != len(chunk):
                print(f'[-]   write: USB write shorter than expected, offset: {offset}')
                exit(1)
            offset += len(chunk)
        except Exception as e:
            print(f'[-]   write: data write offset: {offset} exception: {e}')
            exit(1)
    print(f'[+]   write: USB write done {written}')
    return written


with open(sys.argv[1], "rb") as f:
    file1_data = f.read()

while True:
    dev = usb.core.find(idVendor=VENDOR, idProduct=PRODUCT)
    if dev is not None:
        break
    time.sleep(0.1)
print('[+] device found')

#if dev.is_kernel_driver_active(0):
#    dev.detach_kernel_driver(0)

dev.set_configuration()
#cfg = dev.get_active_configuration()
#intf = cfg[(0, 0)]
#usb.util.claim_interface(dev, 0)
print('[+] device config set')

dat = read()
print(f'[+] got ASIC ID: {dat}')

cmd_bytes = struct.pack("<I", 0xF0030002)
written = write(cmd_bytes)
print(f'[+] boot command OK')

len_bytes = struct.pack("<I", len(file1_data))
written = write(len_bytes)
print(f'[+] length send OK')

written = write(file1_data)
print(f'[+] loader send OK')

print('[+] sleep...')
time.sleep(1)

req = read(13)
#if req != b'USBffile req\x00':
print(f'[+] x-loader file req: {req}')

f = open('dump.bin', 'wb')

for page in range(0, 256*8*(64*2048), 64*2048):
    cmd =  b'USBr'
    loc = struct.pack("<I", page)
    written = write(cmd+loc)
    print(f'[+] CMD2+LOC send OK')

    s = b''
    while True:
        data = read(512)

        if data[:4] == b'xFIN':
            break

        #print(f'[+] x-loader data: {len(data)}')
        s += data

    f.write(s)
    print(f'[+] x-loader data: {len(s)}')
    #print(s)

f.close()
