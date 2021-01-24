#/bin/bash
export LD_LIBRARY_PATH=/usr/local/cuda-10.0/lib64:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
cd /tmp
chmod +x install
if [ -e ias_3.4.gz ]; then
    ./install ias_3.4.gz &
else
    ./install ias_4.1.gz &
fi

if [ -e /usr/local/ev_sdk/bin/test ]; then
    cd /usr/local/ev_sdk/bin
    chmod +x ev_license
    ./ev_license -r r.txt
    ./ev_license -l privateKey.pem r.txt license.txt
    cp /usr/local/ev_sdk/bin/license.txt /usr/local/ias/license_conf.json
else
    cp /usr/local/ev_sdk/3rd/license/bin/ev_license /usr/local/ev_sdk/authorization
    cd /usr/local/ev_sdk/authorization
    chmod +x ev_license
    ./ev_license -r r.txt
    ./ev_license -l privateKey.pem r.txt license.txt
    cp /usr/local/ev_sdk/authorization/license.txt  /usr/local/ev_sdk/bin
    cp /usr/local/ev_sdk/authorization/license.txt /usr/local/ias/license_conf.json
fi
bash /usr/local/ias/ias_stop.sh
bash /usr/local/ias/ias_start_container.sh  &

rm -f /tmp/*



