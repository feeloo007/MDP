# -*- coding: iso-8859-15 -*-
import locale
import re
from contextlib     import closing
from fabric.network import connect

locale.setlocale(locale.LC_ALL, "")

class IntraparisDescriptor:
	@classmethod
	def get_intraparis_descriptor(cls, user, host, port, filenames_descriptor, d_applis ):
		"""get_intraparis_descriptor(cls, user, host, port, filename_descriptor, callbackprocess )
			user : username to remote connection
			host : hostname for remote connection
			port : remote port remote connection
			filenames_descriptor : remote fully qualified filename or list of remote fully qualified filenames
		"""
		with closing(connect(user, host, port)) as ssh:
	    		with closing(ssh.open_sftp()) as sftp:
				if filenames_descriptor.__class__==str: filenames_descriptor = [ filenames_descriptor ]
				for filename_descriptor in filenames_descriptor:
	         			with closing(sftp.open( filename_descriptor )) as f:
						for line in f:
							IntraparisDescriptorToDict.convert_intraparis_descriptor_feed_dict_from_line( line, d_applis )

class IntraparisDescriptorToDict:

	line_pattern='^(?P<MAINCONF>[^\s]*)\s*(?P<MAINSERVERNAME>[^\s]*)\s*(?P<DOMAINNAME>[^\s]*)\s*(?P<HTTPD_USERNAME>[^\s]*)\s*(?P<HTTPD_IP>[^\s]*)\s*(?P<TOMCAT_USERNAME>[^\s]*)\s*(?P<TOMCAT_IP>[^\s]*)\s*(?P<MYSQL_USERNAME>[^\s]*)\s*(?P<MYSQL_IP>[^\s]*)\s*(?P<APP_CODE>\w\w\w)[^\s]*\s*(?P<DEPLOYMENT_SERVERNAME>[^\s]*)\s*(?P<ENV>[^\s]*)\s*(?P<WEBAPP_NAME>[^\s]*)\s*.*$'

	@classmethod
	def convert_intraparis_descriptor_feed_dict_from_line(cls, line, d_applis ):
		d_elements = {}
		#d_elements[ 'Apache' ] = {}
		#d_elements[ 'TOMCAT' ] = {}
		#d_elements[ 'MYSQL' ] = {}

		datas=re.match( cls.line_pattern, line )


		# Obtention du code appli
		app_code =  datas.group('APP_CODE').upper()
		d_applis.setdefault( 
					app_code, 
					{ 
						'desc_app_court': u'Intraparis v2 %s'.encode( 'UTF-8' ) % ( app_code ), 
						'desc_app_long': u'Intraparis v2 %s'.encode( 'UTF-8' ) % ( app_code ), 
						'environnements': {}  
					} 
		)

		# Obtention du type d'environnement
		env = datas.group('ENV')
		d_applis[ app_code ][ 'environnements' ].setdefault( 
			env, 
			{ 
				'composants': [],
				'urls': [], 
				'name_env': u'%s v2'.encode( 'UTF-8' ) % ( env ), 
				'desc_env': u'%s v2'.encode( 'UTF-8' ) % ( env ) 
			} 
		) 

		# Obtention du nom du serveur de déploiement
		deployment_servername = datas.group('DEPLOYMENT_SERVERNAME').replace( 'DEPLOIEMENT-', '')

		# Ajout des éléments.
		# Tous les éléments se trouvent sur le serveur deployment_servername
		# dans le cadre du déploiement intraparis
		d_applis[ app_code ][ 'environnements' ][ env ][ 'composants' ] = {
				'Apache': 
					[ 
						{ 
							'username_composant' : datas.group('HTTPD_USERNAME'),
							'ip_composant': datas.group('HTTPD_IP'),
							'deployment_servername_composant': deployment_servername,
							'name_composant': u'%s'.encode( 'UTF-8' ) % ( datas.group('HTTPD_USERNAME') ),
							'desc_composant': u'écoute sur %s'.encode( 'UTF-8' ) % ( datas.group('HTTPD_IP') ),
							'version_composant' : None
						}
					],
                                'TOMCAT':
					[	
                                        	{
                                                	'username_composant' : datas.group('TOMCAT_USERNAME'),
                                                	'ip_composant': datas.group('TOMCAT_IP'),
                                                	'deployment_servername_composant': deployment_servername,
                                                	'name_composant': u'%s'.encode( 'UTF-8' ) % ( datas.group('TOMCAT_USERNAME') ),
                                                	'desc_composant': u'écoute sur %s'.encode( 'UTF-8' ) % ( datas.group('TOMCAT_IP') ),
                                                	'version_composant' : None
                                        	}
					],
                                'JDK':
					[	
                                        	{
                                                	'username_composant' : datas.group('TOMCAT_USERNAME'),
                                                	'ip_composant': datas.group('TOMCAT_IP'),
                                                	'deployment_servername_composant': deployment_servername,
                                                	'name_composant': u'%s - jdk'.encode( 'UTF-8' ) % ( datas.group('TOMCAT_USERNAME') ),
                                                	'desc_composant': u'écoute sur %s'.encode( 'UTF-8' ) % ( datas.group('TOMCAT_IP') ),
                                                	'version_composant' : None
                                        	}
					],
                                'MYSQL':
                                       	[ 
						{
                                                	'username_composant' : datas.group('MYSQL_USERNAME'),
                                                	'ip_composant': datas.group('MYSQL_IP'),
                                                	'deployment_servername_composant': deployment_servername,
                                                	'name_composant': u'%s'.encode( 'UTF-8' ) % ( datas.group('MYSQL_USERNAME') ),
                                                	'desc_composant': u'écoute sur %s'.encode( 'UTF-8' ) % ( datas.group('MYSQL_IP') ),
                                                	'version_composant' : '5.1.42 @@TEST@@'
                                        	}
					],
			}
			

		main_conf = datas.group('MAINCONF')
		complete_servername = 'http://%s.%s/%s' % ( datas.group('MAINSERVERNAME'), datas.group('DOMAINNAME'), datas.group('WEBAPP_NAME') )
		desc_url = ''
	
		if main_conf == 'OUI':
			desc_url = u'URL principale'.encode( 'UTF-8' )
		else:
			desc_url = u'URL secondaire'.encode( 'UTF-8' )

		d_applis[ app_code ][ 'environnements' ][ env ][ 'urls' ].append(
			{
				'type_url': 'NON WSSO',
				'url': complete_servername,
				'desc_url': desc_url,
			}
		)
