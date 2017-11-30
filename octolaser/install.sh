sudo apt-get install python python-pip virutalenv
git clone --depth 0 https://github.com/foosel/OctoPrint.git
virtualenv octovenv
./octovenv/bin/python setup.py install
./octovenv/bin/octoprint
