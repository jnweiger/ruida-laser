sudo apt-get install python python-pip virtualenv
git clone --depth 1 https://github.com/foosel/OctoPrint.git
cd OctoPrint
virtualenv octovenv
./octovenv/bin/python setup.py install
./octovenv/bin/octoprint
