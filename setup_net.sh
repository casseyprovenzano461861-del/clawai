#!/bin/bash
for iface in eth0 ens33 enp0s3 enp0s8 ens32; do
    ip link set $iface up 2>/dev/null
    dhclient $iface 2>/dev/null &
done
sleep 6
ip addr show > /tmp/ip_result.txt 2>&1
cat /tmp/ip_result.txt
