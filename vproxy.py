#!/usr/bin/env python

'''
 This file is part of Vproxy Project (https://github.com/B4RD4k/Vproxy).
 Version: 1.6
 Copyright (c) 2014-2017 Eran.Vaknin (B4RD4k) eranvak91@gmail.com
'''

import re
import sys
import os
import argparse
import subprocess
from termcolor import colored


def check_root():
	if not os.geteuid() == 0:
		print colored("[!] Vproxy must run as root", "red", attrs=['bold'])
		sys.exit(0)

def user_view(ip,mode,ports,proxy):
	print "[+] Vproxy is running in "+colored(mode,"blue", attrs=['bold'])+" mode..."
	ans = raw_input("[+] SSL certificate is installed properly on the mobile device (Y/N)? ").lower()
	if (ans == "yes" or ans == "y"):
		proc1 = subprocess.Popen("sudo bash vconfig.sh", shell=True, stdout=subprocess.PIPE).stdout.read()
		print ""
		if (mode == "redirect"):
			print colored("[+]Vconfig output:",attrs=['bold'])
			print colored("  [-] Intercepting port: ",attrs=['bold']) + colored(ports, "blue", attrs=['bold'])
			print colored("  [-] Redirecting to proxy: ",attrs=['bold']) + colored(proxy, "blue", attrs=['bold'])
			subprocess.Popen("sudo wireshark", shell=True, stdout=subprocess.PIPE)
			print ""
		print colored("[-] ","yellow", attrs=['bold']) + colored("VPN server address: ",attrs=['bold']) + colored(ip,"blue", attrs=['bold'])
		print colored("[-] ","yellow", attrs=['bold']) + colored("Username: ",attrs=['bold']) + colored("Vuser","blue", attrs=['bold'])
		print colored("[-] ","yellow", attrs=['bold']) + colored("Password: ",attrs=['bold']) + colored("Vpassword","blue", attrs=['bold'])
		print ""
		print colored("~~~~~~~Lets Rock!~~~~~~~~","yellow",attrs=['bold'])
		print ""
		try:
			raw_input("[!] Press any to stop Vproxy...")
			cleanup()
		except KeyboardInterrupt:
			cleanup()
	else:
		print colored("[!] Check arguments and try again", "red", attrs=['bold'])
		sys.exit(0)

def cleanup():
	print ""
	print ("[!] Exiting now...")
	subprocess.Popen("service pptpd stop", shell=True, stdout=subprocess.PIPE).stdout.read()
	subprocess.Popen("ifconfig ppp0 down", shell=True, stdout=subprocess.PIPE).stdout.read()
	subprocess.Popen("iptables -t nat -F", shell=True, stdout=subprocess.PIPE).stdout.read()
	subprocess.Popen("sudo killall wireshark", shell=True, stdout=subprocess.PIPE).stdout.read()

def print_logo():
	logo = '''
	'##::::'##:'########::'########:::'#######::'##::::'##:'##:::'##:
	 ##:::: ##: ##.... ##: ##.... ##:'##.... ##:. ##::'##::. ##:'##::
	 ##:::: ##: ##:::: ##: ##:::: ##: ##:::: ##::. ##'##::::. ####:::
	 ##:::: ##: ########:: ########:: ##:::: ##:::. ###::::::. ##::::
	. ##:: ##:: ##.....::: ##.. ##::: ##:::: ##::: ## ##:::::: ##::::
	:. ## ##::: ##:::::::: ##::. ##:: ##:::: ##:: ##:. ##::::: ##::::
	::. ###:::: ##:::::::: ##:::. ##:. #######:: ##:::. ##:::: ##::::
	:::...:::::..:::::::::..:::::..:::.......:::..:::::..:::::..:::::
	'''
	print logo

def check_args(arguments):
	#Debug Arguments
	#print arguments

	regex_ip = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
	regex_proxy = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):[0-9]+$"
	a_mode = arguments.mode.lower()
	if(arguments.port):
		ismonitor = True
		a_port = arguments.port.split(",")
	else:
		ismonitor = False
		a_port = None

	if (ismonitor):
		for port in a_port:
			if (int(port) > 65536):
				print colored("[!] Check arguments and try again", "red", attrs=['bold'])
				sys.exit(0)
	if(re.match(regex_ip,arguments.ip)):
		if(arguments.proxy and re.match(regex_proxy, arguments.proxy)):
			if(a_mode == "r" or a_mode == "redirect"):
				#Start redirect mode
				do_vproxy(arguments.ip,a_port,a_mode,arguments.proxy)
				user_view(arguments.ip,"redirect",a_port,arguments.proxy)
			else:
				print colored("[!] Check arguments and try again", "red", attrs=['bold'])
				sys.exit(0)
		else:
			if (a_mode == "m" or a_mode == "monitor"):
				#Start monitor mode
				do_vproxy(arguments.ip,a_port,a_mode,None)
				user_view(arguments.ip,"monitor",None,None)
			else:
				print colored("[!] Check arguments and try again", "red", attrs=['bold'])
				sys.exit(0)
	else:
		print colored("[!] Check arguments and try again", "red", attrs=['bold'])
		sys.exit(0)

def do_vproxy(ip,ports,mode,proxy):
	if (os.path.exists('vconfig.sh')):
		os.remove('vconfig.sh')
	f = open('vconfig.sh', 'w')
	f.write('apt-get -y install pptpd\n')
	f.write('sudo apt-get -y install wireshark\n')
	f.write('sleep 2\n')
	f.write('iptables -t nat -F\n')
	if (mode == "r" or mode == "redirect" ):
		for port in ports:
			f.write('iptables -t nat -A PREROUTING -p tcp -s 192.168.2.0/24 --dport ' + port + ' -j DNAT --to-destination ' + proxy.split(':')[0] + ':' + proxy.split(':')[1] + '\n')
	f.write('sysctl -w net.ipv4.ip_forward=1\n')
	f.write('iptables -t nat -A POSTROUTING -j MASQUERADE\n')
	f.write('cat >/etc/ppp/chap-secrets <<END\n')
	f.write('Vuser pptpd Vpassword *\n')
	f.write('END\n')
	f.write('cat >/etc/pptpd.conf <<END\n')
	f.write('option /etc/ppp/options.pptpd\n')
	f.write('localip 192.168.2.1\n')
	f.write('remoteip 192.168.2.10-30\n')
	f.write('END\n')
	f.write('cat >/etc/ppp/options.pptpd <<END\n')
	f.write('name pptpd\n')
	f.write('refuse-pap\n')
	f.write('refuse-chap\n')
	f.write('refuse-mschap\n')
	f.write('require-mschap-v2\n')
	f.write('require-mppe-128\n')
	f.write('ms-dns 8.8.8.8\n')
	f.write('proxyarp\n')
	f.write('lock\n')
	f.write('nobsdcomp \n')
	f.write('novj\n')
	f.write('novjccomp\n')
	f.write('mtu 1490\n')
	f.write('mru 1490\n')
	f.write('nologfd\n')
	f.write('END\n')
	f.write('sleep 4\n')
	f.write('sudo service pptpd restart\n')
	f.close()

def main():
	print_logo()

	#Parse User Arguments
	parser = argparse.ArgumentParser(description='Use Vproxy to sniff or redirect your mobile traffic to any proxy instance easily')
	bgroup = parser.add_argument_group("Basic Parameters")
	bgroup.add_argument('-ip', help='Local IP', required=True)
	bgroup.add_argument('-port', help='Which port/s do you want to sniff? 80,443...')
	bgroup = parser.add_argument_group("Advanced Parameters")
	bgroup.add_argument('-proxy', help='The Proxy Instance ($HOST:$PORT)')
	bgroup.add_argument('-mode', help='Monitor (M) or Redirect (R)', required=True)

	#Check for default behavior
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	args = parser.parse_args()

	#Check for root privileges
	check_root()

	#Check arguments from user and start Vproxy
	check_args(args)

if __name__ == '__main__':
	main()
