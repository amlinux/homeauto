all: novatorskaya.html novatorskaya-len.html novatorskaya.labels.csv novatorskaya-byroom.html

novatorskaya-len.html: novatorskaya.conn wireslist.pl WiresList/*.pm
	./wireslist.pl --input novatorskaya.conn --output novatorskaya-len.html

novatorskaya.html: novatorskaya.conn wireslist.pl WiresList/*.pm
	./wireslist.pl --input novatorskaya.conn --output novatorskaya.html --hide-length

novatorskaya-byroom.html: novatorskaya.conn wireslist.pl WiresList/*.pm
	./wireslist.pl --input novatorskaya.conn --output novatorskaya-byroom.html --cables-by-room --hide-areas --hide-length

novatorskaya.labels.csv: novatorskaya.conn labels.pl WiresList/*.pm
	./labels.pl --input novatorskaya.conn --output novatorskaya.labels.csv
