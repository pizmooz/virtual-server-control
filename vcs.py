#!/usr/bin/python
import sys
import os
import subprocess
import json


def print_help():

	print """

echo "{command: 'init', type: 'rails'}" | vsrvctl

vsrvctl 
		init
				[html]
				rails
				php
				node
		server
				[status]
				start
				restart
				stop
				status
		help

"""

class VirtualServer:

	Templates = {

		'html' : """
			server {{
			    listen          80;
			    server_name     {name}.*;
			 
			    index           index.html;
			    root            {root_path}/public;
				}}
		""",

		'php': """
			server {{
			    listen          80;
			    server_name     {name}.*;
			 
			    index           index.php;
			    root            {root_path};
			 
			    location / {{
			        try_files   $uri $uri/ /index.php;
			    }}
			 
			    location ~* \.php$ {{
			        include fastcgi.conf; # I include this in http context, it's just here to show it's required for fastcgi!
			        try_files $uri =404;
			        fastcgi_pass 127.0.0.1:9000;
			    }}
			}}

		""",

		'rails': """
			server {{
				listen 80;
				server_name {name}.*;
				root {root_path}/public;
				rails_env development;
				passenger_enabled on;

			}}
		""",

		'node':"""

			server {{
				listen			80;
				server_name		%(name).*
				location / {{ 
					proxy_pass http://127.0.0.1 %(internal-port)
					expires 30d;
					access_log off; }}
				location ~* ^.+\.(jpg|jpeg|gif|png|ico|css|zip|tgz|gz|rar|bz2|pdf|txt|tar|wav|bmp|rtf|js|flv|swf|html|htm)$ {
			        root   /var/www/yoursitename/public;
			    }}
		"""

	}

	def __init__(self):

		self.gen_default_data()
		self.load_data()


	def _nginx_reload(self):

		
		ret=subprocess.call( [ "/opt/nginx/sbin/nginx" ,  "-s" , "reload" ] )
		if ret!=0:
			raise "error communicating with nginx, ensure that nginx is running"


	def gen_config(self,tp):
		
		F=open('./nginx.conf','w')

		print self.__dict__

		F.write(self.Templates[tp].format( **self.__dict__ ) )

		F.close()

	def gen_default_data(self):

		curdir=os.getcwd()
		self.name = os.path.basename(curdir)
		self.root_path= curdir		


	def load_data(self):


		try:
			F=open('vs.json')
			data=json.load(F)
			F.close()
			for k in data:
				setattr(self,k,data[k])
		except:
			print 'no config file found using defaults'
			pass

	def control(self,com):

		if com=='start' : self.start()
		elif com=='stop' : self.stop()
		elif com=='restart': self._nginx_reload()


	def execute(self,command_list):

		try:
			command=command_list[0]
		except:
			raise 'you must supply a command'

		if command=='init':
			
			try:
				server_type=command_list[1]
			except:
				server_type='html'

			if server_type in ('html','rails','node','php'):
				VS.gen_config(server_type)
			else:
				raise 'invalid server type'

		elif command=='control':

			try:
				subcommand=command_list[1]
			except:
				subcommand='status'

			if subcommand in ('start','stop','restart','status'):
				VS.control(subcommand)
			else:
				raise 'invalid subcommand'

		elif command in ('start','stop','restart','status'):
			VS.control(command)

		else:

			show_help()

	def start(self):
		
		try:
			os.symlink("./nginx.conf","./.nginx.conf.enabled")
		except:
			print "could not access files, you may need to run init first , check your nginx.conf file name"

		self._nginx_reload()

	def stop(self):
		
		try:
			os.remove("./.nginx.conf.enabled")
		except:
			print "could not access files, you may need to run init first , check your nginx.conf file name"

		self._nginx_reload()

	def restart(self):
		
		self._nginx_reload()


VS=VirtualServer()
VS.execute(sys.argv[1:])



