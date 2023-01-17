To install/activate the service

cp novaprox.service /etc/systemd/system/
mkdir /root/scripts
cd    /root/scripts
ln -s /root/src/github/jnweiger/ruida-laser/RuidaProxy/novaprox-start.sh .

systemctl enable novaprox.service
systemctl start  novaprox.service
systemctl status novaprox.service

This starts a screen session
to attach to the screen execute
screen -x

