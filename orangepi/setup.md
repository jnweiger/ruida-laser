grep -q nova35_fablabnbg /etc/hosts || sudo tee <<EOF -a /etc/hosts > /dev/null
#
# lasers for proxy23
192.168.2.21 nova35_falafue
172.18.16.11 nova35_fablabnbg
EOF

nmtui
 -> ethernet nova35_falafue,   eth0,  192.168.2.23/23, gw 192.168.2.1, dns 8.8.8.8
 -> ethernet nova35_fablabnbg, eth0,  172.18.16.23/24, ? gw 172.18.16.254 ?, dns 8.8.8.8
 -> wifi jw_hotspot,           wlan0, jw samsung s4, ******, ipv4 automatic

ps -ef | grep dhclient
 ... eth0
 ... wlan0

# need to switch off dhclient on eth0, before we can activate any of the other configs...

vi /etc/network/interfaces
 # Wired adapter #1
 allow-hotplug eth0
 no-auto-down eth0
 #iface eth0 inet dhcp   # dhclient on eth0???
ZZ
reboot
# now we can activate a static ethernet config.
