import sys
import usb.core
import usb.util
import struct
import time

cmd = {
    "GET_ID":       0xF0030003,

    "BOOT":         0xF0030002,
    "BOOT_VOID":    0xF0030006,
    "BOOT_XIP":     0xF0030106,
    "BOOT_XIPWAIT": 0xF0030206,
    "BOOT_NAND":    0xF0030306,
    "BOOT_OneNAND": 0xF0030406,
    "BOOT_MMC1":    0xF0030506,
    "BOOT_MMC2_1":  0xF0030606,
    "BOOT_MMC2_2":  0xF0030706,
    "BOOT_EMFI":    0xF0030806,

    "BOOT_UART3":   0xF0034306,
    "BOOT_USB":     0xF0034506,
    "BOOT_USB":     0xF0034606,

    "BOOT_NEXT":    0xFFFFFFFF
}

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

    print(f'[+]   read: USB read OK, len: {len(data)}')
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

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <x-load> <uboot> <initrd>")
    exit(1)

with open(sys.argv[1], "rb") as f:
    file1_data = f.read()

with open(sys.argv[2], "rb") as f:
    file2_data = f.read()

with open(sys.argv[3], "rb") as f:
    file3_data = f.read()

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

cmd_bytes = struct.pack("<I", cmd['BOOT'])
written = write(cmd_bytes)
print(f'[+] boot command OK')

len_bytes = struct.pack("<I", len(file1_data))
written = write(len_bytes)
print(f'[+] length send OK')

written = write(file1_data)
print(f'[+] loader send OK')

print('[+] sleep...')
time.sleep(1)

print('\n ========== send uboot')
req = read(13)
#if req != b'USBffile req\x00':
print(f'[+] x-loader file req: {req}')

cmd =  b'USBs'
len_bytes = struct.pack("<I", len(file2_data))
addr = struct.pack("<I", 0x80100000)
written = write(cmd+len_bytes+addr)
print(f'[+] CMD2+LEN+OFFSET send OK')

data = read(8)
len_expect = struct.unpack("<I", data[4:])[0]
print(f'[+] x-loader {data}: {len_expect}')

written = write(file2_data)
print(f'[+] FILE2 send OK')

data = read(8)
len_expect = struct.unpack("<I", data[4:])[0]
print(f'[+] x-loader {data}: {len_expect}')



print('\n ========== send initrd')
data = read(512)
print(f'[+] x-loader file req: {data}')

cmd =  b'USBs'
len_bytes = struct.pack("<I", len(file3_data))
addr = struct.pack("<I", 0x81400000)
written = write(cmd+len_bytes+addr)
print(f'[+] CMD2+LEN+OFFSET send OK')

data = read(8)
len_expect = struct.unpack("<I", data[4:])[0]
print(f'[+] x-loader {data}: {len_expect}')

written = write(file3_data)
print(f'[+] FILE3 send OK')

data = read(8)
len_expect = struct.unpack("<I", data[4:])[0]
print(f'[+] x-loader {data}: {len_expect}')



print('\n ========== send jump')
data = read(512)
print(f'[+] x-loader file req: {data}')

written = write(b'USBj' + struct.pack("<I", 0x80100000))
print(f'[+] JUMP send OK')
