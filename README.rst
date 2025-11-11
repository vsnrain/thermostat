# 0 disclaimer
#################################

not affiliated with nest labs or google.
rejected for fulu bounty

Proof of concept with device SSH access and custom backend

check releases for prebuilt binaries

python3 boot.py x-load.bin u-boot.bin uInitrd
<hold 10 sec>
<wait boot>
<connect wifi>
ncat -v <ip> 1337

feel free to donate if you would like non-US residents to be rewarded for their work
BTC bc1qd2ed02lwket6gnjmmhjdagexjgn5wejnugksdk

# 1 building x-load
#################################

# changes:
# - increase timeout to 20s
# - add feature to dump nand through x-loader

chmod +x tools/setlocalversion
chmod +x tools/scripts/make-asm-offsets

make j49-usb-loader_config
make

# 2 building u-boot
#################################

# changes:
# - add initrd to boot options

export CROSS_COMPILE=arm-none-eabi-
export PATH=/opt/gcc-arm-none-eabi-4_9-2015q3/bin:$PATH

make j49-usb-loader_config
make j49_config
make

# 3 root
#################################
python3 boot.py x-load.bin u-boot.bin uInitrd
<hold 10 sec>
<wait boot>
<connect wifi>
ncat -v <ip> 1337

# 3 custom backend
#################################

(on device)
vi /nestlabs/etc/client.config
set cloudregisterurl to your local server

cd ./server
pip3 install fastapi uvicorn python-multipart
python3 main.py
