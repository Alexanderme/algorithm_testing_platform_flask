#!/bin/bash
# 授权
cp /usr/local/ev_sdk/3rd/license/bin/ev_license /usr/local/ev_sdk/authorization
cd /usr/local/ev_sdk/authorization
chmod +x ev_license
./ev_license -r r.txt
./ev_license -l privateKey.pem r.txt license.txt

cp /usr/local/ev_sdk/authorization/license.txt  /usr/local/ev_sdk/bin

cp -r /tmp/$1 /usr/local/ev_sdk/bin/1.jpg
#cd /usr/local/ev_sdk/bin
#./test-ji-api -f 1 -i 1.jpg -r 100000

