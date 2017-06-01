#!/usr/bin/python
import sys
from requests import get

if __name__ == '__main__':
	try:
		r = get(sys.argv[1])
		if r.status_code != 200:
			print "Error retrieving config file at {0}.".format(sys.argv[1])
			quit(1)
		else:
			print "Successfully feteched config file."
		i = 1
		for ip in r.text.split():
			a = get(ip)
			if r.status_code != 200:
				print "Error retrieving config file at {0}.".format(ip)
				quit(1)
			else:
				print "Successfully feteched config file." 
				with open('/etc/modsecurity/rules/{0}.conf'.format(str(i)),'w') as f:
					f.write(a.text)
	except Exception as e:
		print "Error retrieving config files: {0}".format(str(e))
		quit(1)
	else:
		quit(0)