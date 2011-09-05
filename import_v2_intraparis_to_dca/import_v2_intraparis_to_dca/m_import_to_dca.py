# -*- coding: iso-8859-15 -*-
import locale
from contextlib import closing
from urllib import urlencode
from httplib import HTTPConnection
from lxml.etree import fromstring,tostring
from html5lib import HTMLParser
from html5lib import treebuilders
import re
from m_import_to_dca_deals_with_versions import deals_with_version
import copy
from colors import *
import sys

locale.setlocale(locale.LC_ALL, "")

class deal_with_loop(object):
	def __init__( self, triplet_indexes ):
		# triplet_indexes est un liste contenant
		# en premier paramètre, l'objet instancié à partir de ImportToDCA
		# en second paramètre, une chaine de caractère contenant le nom du paramètre
		# définissant si la boucle est active
		# en troisieme paramètre, une chaine de caractère contenant le nom du 
		# paramètre contenant les références déjà créées / récupéréés

       		self._triplet_indexes	  	= triplet_indexes
       		self._i2dca		  	= triplet_indexes[0]
                self._is_on_loop_sav 	 	= getattr( self._i2dca, self._triplet_indexes[1] )

		if self._triplet_indexes[2].__class__ == dict:
                	self._sav          	= getattr( self._i2dca, self._triplet_indexes[2] ).copy()
		elif self._triplet_indexes[2].__class__ == list:
			self._sav               = getattr( self._i2dca, self._triplet_indexes[2][ : ] )
		else:
			self._sav		= getattr( self._i2dca, copy.copy( self._triplet_indexes[2] ) )	
		setattr( self._i2dca, triplet_indexes[1], True )

        def __enter__( self ):
                return self

        def __exit__( self, *exc_info ):

		setattr( self._i2dca, self._triplet_indexes[1], self._is_on_loop_sav )

		if self._sav.__class__ == dict:
			setattr( self._i2dca, self._triplet_indexes[2], self._sav.copy() )
		elif self._sav.__class__ == list:
			setattr( self._i2dca, self._triplet_indexes[2], self._sav[ : ] )
		else:
			setattr( self._i2dca, self._triplet_indexes[2], copy.copy( self._sav ) )



class ImportToDCA:

	_d_namespaces = { 'html': 'http://www.w3.org/1999/xhtml' }
	_headers = { 'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain' }
	_deals_with_version_default_funcname = 'reject_unknown_version_for_type_composant'

	def set_cookie_membre( self, cookie_membre ):
		self._cookie_membre = cookie_membre
		if self._cookie_membre is not None:
			self._headers[ 'Cookie' ] = 'cookie_membre=%s' % ( cookie_membre )

	def set_dca_servername( self, dca_servername ):
		self._dca_servername = dca_servername

	def __init__( self, dca_servername = None, cookie_membre = None, deals_with_version_funcname = _deals_with_version_default_funcname ):
		self._httpconn = None

		self._print_debug = True

		# Dictionnaire stockant des référentiels
		self._d_env_ref = None
		self._d_type_composant_ref = None

		self._deals_with_version_default_funcname = deals_with_version_funcname

		# Gestion des boucles d'apels
		# dictionnaire contenant les app_code déjà créé / vérifié
		self._d_app_on_loop_created = {}
		# indique si la création d'application est dans une boucle
		self._is_app_on_loop = False
		# dictionnaire contenant les triplet ( app_code, type_env, name_env ) déjà créées / vérifiées
                self._d_env_on_loop_created = {}
                # indique si la création d'environnement est dans une boucle
                self._is_env_on_loop = False
		# dictionnaire contenant les doublets ( type_composant, version_composant ) déjà créées / vérifiées
		self._d_version_on_loop_created = {}
		# indique si la création de version est dans une boucle
                self._is_version_on_loop = False
		# objet stockant le selectionneur de version
		self._l_dwv = {}
		# indique si le secltionneur de version est dans une boucle
		self._is_deals_with_versions_on_loop = False
		 
		# Initialisation des données techniques de connexions
		self.set_dca_servername( dca_servername )
		self.set_cookie_membre( cookie_membre )

	#############
	# INTERCEPTOR
	#############

        def process_with_httpconn_loaded_interceptor( func ):
                """ Decorateur :
                        - vérifiant que le nom de serveu a bien été fourni
                        - l'identifiant cookie_membre a bien été fourni
                        - si l'objet self.httpconn est ouvert ou non
                                - si il est ouvert, le code est directement exécuté
                                - si il n'est pas ouvert, le code est placé dans un bloc with closing pour
                                  être fermé en fin de traitement
                """
                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print white( '@%s(%s)\t|%s| <-' ) % ( self.process_with_httpconn_loaded_interceptor.func_name, func.func_name, 'process_with_httpconn_loaded_interceptor.wrapped' )

			result = None

                        if not self._dca_servername:
                                raise ValueError( 'servername non défini' )

                        if not self._cookie_membre:
                                raise ValueError( 'cookie_membre non défini' )

                        if not self._httpconn:
                                self._httpconn = self.create_htttp_conn( *args, **kwargs )
                                with closing( self._httpconn ):
                                        result = func( self, *args, **kwargs )
                                self._httpconn = None
                        else:
                                result = func( self, *args, **kwargs )

			if self._print_debug: print white( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_httpconn_loaded_interceptor.func_name, func.func_name, 'process_with_httpconn_loaded_interceptor.wrapped', result )

                        return result

                return wrapped


	def process_with_env_ref_loaded_interceptor( func ):
		""" Décorateur valorisant la variable self_.d_env_ref pour la fonction utilisée"""
                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print red( '@%s(%s)\t|%s| <-' ) % ( self.process_with_env_ref_loaded_interceptor.func_name, func.func_name, 'process_with_env_ref_loaded_interceptor.wrapped' )

			result = None

			if not self._d_env_ref:
				# Avant traitement, créé le référentiel au besoin"
				self._d_env_ref = self.load_env_ref( *args, **kwargs )

				result = func( self, *args, **kwargs )

				# Après traitement, détruit le référentiel
				self._d_env_ref = None
			else:
				# Si le référentiel existait, on ne fait que le traitement
				# Surtout, on ne détruit pas le référentiel
				result = func( self, *args, **kwargs )

			if self._print_debug: print red( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_env_ref_loaded_interceptor.func_name, func.func_name, 'process_with_env_ref_loaded_interceptor.wrapped', result )

			return result

                return wrapped


        def app_created_on_loop_interceptor( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print green( '@%s(%s)\t|%s| <-' ) % ( self.app_created_on_loop_interceptor.func_name, func.func_name, 'app_created_on_loop_interceptor.wrapped' )

			result = None

                        with deal_with_loop( [ self, '_is_app_on_loop', '_d_app_on_loop_created' ] ):

                                result = func( self, *args, **kwargs )

				if self._print_debug: print green( '@%s(%s)\t|%s| -> %s' ) % ( self.app_created_on_loop_interceptor.func_name, func.func_name, 'app_created_on_loop_interceptor.wrapped', result )

				return result

                return wrapped


        def create_app_if_needed( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print green( '@%s(%s)\t|%s| <-' ) % ( self.create_app_if_needed.func_name, func.func_name, 'create_app_if_needed.wrapped' )

                        result = None

	                app_code = kwargs[ 'app_code' ]

			if self._is_app_on_loop:
				if app_code not in self._d_app_on_loop_created.keys():
                        		self.create_app( *args, **kwargs )
					self._d_app_on_loop_created[ app_code ] = app_code

			result = func( self, *args, **kwargs )

			if self._print_debug: print green( '@%s(%s)\t|%s| -> %s' ) % ( self.create_app_if_needed.func_name, func.func_name, 'create_app_if_needed.wrapped', result )

                        return result

                return wrapped


        def process_with_app_exists_interceptor( attempt ):
                """ d?corateur r?alisant la fonction func si l'existence
                    de l'env est ? la valeur attempt"""
                def wrapper( func ):

                        def wrapped( self, *args, **kwargs ):

				if self._print_debug: print green( '@%s(%s)\t|%s| <-' ) % ( self.process_with_app_exists_interceptor.func_name, func.func_name, 'process_with_app_exists_interceptor.wrapper.wrapped' )

				result = None

		                app_code = kwargs[ 'app_code' ]

                                result = None
				app_exists = False
	                        if self._is_app_on_loop:
                                	if app_code in self._d_app_on_loop_created.keys():
						app_exists = True
					else:
						app_exists = self.app_exists( *args, **kwargs )
				else:
					app_exists = self.app_exists( *args, **kwargs )

				if app_exists:
					self._d_app_on_loop_created[ app_code ] = app_code

                                if app_exists == attempt:
                                        result = func( self, *args, **kwargs )

				if self._print_debug: print green( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_app_exists_interceptor.func_name, func.func_name, 'process_with_app_exists_interceptor.wrapper.wrapped', result )

				return result

                        return wrapped

                return wrapper


        def env_created_on_loop_interceptor( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print red( '@%s(%s)\t|%s| <-' ) % ( self.env_created_on_loop_interceptor.func_name, func.func_name, 'env_created_on_loop_interceptor.wrapped' )

			result = None

                        with deal_with_loop( [ self, '_is_env_on_loop', '_d_env_on_loop_created' ] ):

                                result = func( self, *args, **kwargs )
				if self._print_debug: print red( '@%s(%s)\t|%s| -> %s' ) % ( self.env_created_on_loop_interceptor.func_name, func.func_name, 'env_created_on_loop_interceptor.wrapped', result )
				return result

                return wrapped


        def create_env_for_app_if_needed( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print red( '@%s(%s)\t|%s| <-' ) % ( self.create_env_for_app_if_needed.func_name, func.func_name, 'create_env_for_app_if_needed.wrapped' )

                        result = None

	                app_code = kwargs[ 'app_code' ]
        	        type_env = kwargs[ 'type_env' ]
                	name_env = kwargs[ 'name_env' ]

			id_env = 0

			key_env = 'APP=%s,TYPE_ENV=%s,NAME_ENV=%s' %( app_code, type_env, name_env)

                        if self._is_env_on_loop:
                                if key_env not in self._d_env_on_loop_created.keys():
                        		id_env = self.create_env_for_app( *args, **kwargs )
                                        self._d_env_on_loop_created[ key_env ] = id_env

                        result = func( self, *args, **kwargs )

			if self._print_debug: print red( '@%s(%s)\t|%s| -> %s' ) % ( self.create_env_for_app_if_needed.func_name, func.func_name, 'create_env_for_app_if_needed.wrapped', result )
                        return result

                return wrapped


	def process_with_env_exists_interceptor( attempt ):
		""" décorateur réalisant la fonction func si l'existence
		    de l'env est à la valeur attempt"""
		def wrapper( func ):

			def wrapped( self, *args, **kwargs ):

				if self._print_debug: print red( '@%s(%s)\t|%s| <-' ) % ( self.process_with_env_exists_interceptor.func_name, func.func_name, 'process_with_env_exists_interceptor.wrapper.wrapped' )

				result = None

		                app_code = kwargs[ 'app_code' ]
                		type_env = kwargs[ 'type_env' ]
                		name_env = kwargs[ 'name_env' ]

				env_exists = False

				key_env = 'APP=%s,TYPE_ENV=%s,NAME_ENV=%s' %( app_code, type_env, name_env)

				if self._is_env_on_loop:
					if key_env in self._d_env_on_loop_created.keys():
						result = self._d_env_on_loop_created[ key_env ]
						env_exists = True 
					else:
						try:
                                       			result = self.get_id_env_for_app( *args, **kwargs )
                                       	 		env_exists = True
							self._d_env_on_loop_created[ key_env ] = id_env
                                		except:
							pass
				else:
                        		try:
                        			result = self.get_id_env_for_app( *args, **kwargs )
						env_exists = True 
                        		except:
                                		pass

				if env_exists == attempt:
					result = func( self, *args, **kwargs )

				if self._print_debug: print red( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_env_exists_interceptor.func_name, func.func_name, 'process_with_env_exists_interceptor.wrapper.wrapped', result )

				return result

			return wrapped

		return wrapper


        def process_with_type_composant_ref_loaded_interceptor( func ):
                """ Décorateur valorisant la variable self_._d_type_composant_ref pour la fonction utilisée"""
                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print cyan( '@%s(%s)\t|%s| <-' ) % ( self.process_with_type_composant_ref_loaded_interceptor.func_name, func.func_name, 'process_with_type_composant_ref_loaded_interceptor.wrapped' )

			result = None

                        if not self._d_type_composant_ref:
                                # Avant traitement, créé le référentiel au besoin
                                self._d_type_composant_ref = self.load_type_composant_ref( *args, **kwargs )

                                result = func( self, *args, **kwargs)

                                # Après traitement, détruit le référentiel
                                self._d_type_composant_ref = None
                        else:
                                # Si le référentiel existait, on ne fait que le traitement
                                # Surtout, on ne détruit pas le référentiel
                                result = func( self, *args, **kwargs)

			if self._print_debug: print cyan( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_type_composant_ref_loaded_interceptor.func_name, func.func_name, 'process_with_type_composant_ref_loaded_interceptor.wrapped', result )

                        return result

                return wrapped


        def process_with_version_for_type_composant_loaded_interceptor( func ):
		""" Décorateur valorisant la variable self_._d_type_composant_ref [ type_composant ]
		    type_composant étant passé par la variables kwargs"""
                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.process_with_version_for_type_composant_loaded_interceptor.func_name, func.func_name, 'process_with_version_for_type_composant_loaded_interceptor.wrapped' )

	                result = None

			type_composant = kwargs[ 'type_composant' ]

	                if not self._d_type_composant_ref[ type_composant ][ 'versions' ]:
				print '\t\tRécupération de self._d_type_composant_ref[ %s ]' % ( type_composant )	
				self._d_type_composant_ref[ type_composant ][ 'versions' ] = self.get_all_id_version_for_type_composant( *args, **kwargs )
                      		result = func( self, *args, **kwargs)
                      	else:
                      		result = func( self, *args, **kwargs)

			if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_version_for_type_composant_loaded_interceptor.func_name, func.func_name, 'process_with_version_for_type_composant_loaded_interceptor.wrapped', result )

                      	return result

                return wrapped


        def version_for_type_composant_created_on_loop_interceptor( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.version_for_type_composant_created_on_loop_interceptor.func_name, func.func_name, 'version_for_type_composant_created_on_loop_interceptor.wrapped' )

			result = None

                        with deal_with_loop( [ self, '_is_version_on_loop', '_d_version_on_loop_created' ] ):

                                result = func( self, *args, **kwargs )

				if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.version_for_type_composant_created_on_loop_interceptor.func_name, func.func_name, 'version_for_type_composant_created_on_loop_interceptor.wrapped', result )

                                return result

                return wrapped


        def create_version_for_type_composant_if_needed( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.create_version_for_type_composant_if_needed.func_name, func.func_name, 'create_version_for_type_composant_if_needed.wrapped' )

			result = None

			type_composant 		= kwargs[ 'type_composant' ]
			version_composant 	= kwargs[ 'version_composant' ]
			key_version_composant   = 'TYPE_COMPOSANT=%s,VERSION_COMPOSANT=%s' % ( type_composant, version_composant )

			print 'create_version_for_type_composant_if_needed %s' % version_composant

                        id_version = 0

                        if self._is_version_on_loop:
                                if key_version_composant not in self._d_version_on_loop_created.keys():
                                        id_version = self.create_version_for_type_composant( *args, **kwargs )
                                        self._d_version_on_loop_created[ key_version_composant ] = id_version

                        result = func( self, *args, **kwargs )

			if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.create_version_for_type_composant_if_needed.func_name, func.func_name, 'create_version_for_type_composant_if_needed.wrapped', result )

                        return result

                return wrapped


        def process_with_version_for_type_composant_exists_interceptor( attempt ):
                """ décorateur réalisant la fonction func si l'existence
                    de la version est à la valeur attempt"""
                def wrapper( func ):

                        def wrapped( self, *args, **kwargs ):

				if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.process_with_version_for_type_composant_exists_interceptor.func_name, func.func_name, 'process_with_version_for_type_composant_exists_interceptor.wrapper.wrapped' )

                                result = None

				print kwargs

				type_composant 		= kwargs[ 'type_composant' ]
				version_composant 	= kwargs[ 'version_composant' ]
				key_version_composant   = 'TYPE_COMPOSANT=%s,VERSION_COMPOSANT=%s' % ( type_composant, version_composant )

				print self._d_version_on_loop_created
				print type_composant
				print version_composant
				print key_version_composant

                                version_exists = False
				l_versions = None
                                if self._is_version_on_loop:
                                        if key_version_composant in self._d_version_on_loop_created.keys():
                                                version_exists = True
                                        else:
						l_versions = self.get_all_id_version_for_type_composant( *args, **kwargs )
						version_exists = version_composant in l_versions
                                else:
					l_versions = self.get_all_id_version_for_type_composant( *args, **kwargs )
					version_exists = version_composant in l_versions

                                if version_exists:
                                        self._d_version_on_loop_created[ key_version_composant ] = version_composant

                                if version_exists == attempt:
                                        result = func( self, *args, **kwargs )

				print self._d_version_on_loop_created
				if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.process_with_version_for_type_composant_exists_interceptor.func_name, func.func_name, 'process_with_version_for_type_composant_exists_interceptor.wrapper.wrapped', result )

                                return result

                        return wrapped

                return wrapper


        def deals_with_versions_for_type_composant_on_loop_interceptor( func ):

                def wrapped( self, *args, **kwargs ):

			if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.deals_with_versions_for_type_composant_on_loop_interceptor.func_name, func.func_name, 'deals_with_versions_for_type_composant_on_loop_interceptor.wrapped' )

			result = None

                        with deal_with_loop( [ self, '_is_deals_with_versions_on_loop', '_l_dwv' ] ):

                                result = func( self, *args, **kwargs )

				if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.deals_with_versions_for_type_composant_on_loop_interceptor.func_name, func.func_name, 'deals_with_versions_for_type_composant_on_loop_interceptor.wrapped', result )

                                return result

                return wrapped


	def filter_versions_for_type_composant_interceptor( func ):

		def wrapped( self, *args, **kwargs ):

			if self._print_debug: print yellow( '@%s(%s)\t|%s| <-' ) % ( self.filter_versions_for_type_composant_interceptor.func_name, func.func_name, 'filter_versions_for_type_composant_interceptor.wrapped' )

			deals_with_version_funcname = kwargs.get( 'deals_with_version_funcname', self._deals_with_version_default_funcname )

			result = None

			dwv = None

			if self._is_deals_with_versions_on_loop:
				if not self._l_dwv.get( deals_with_version_funcname ):
					self._l_dwv [ deals_with_version_funcname ] = deals_with_version( [ self, deals_with_version_funcname ] )
				dwv = self._l_dwv [ deals_with_version_funcname ] 
			else:
				dwv = deals_with_version( [ self, deals_with_version_funcname ] )

			result = None
			selected_version = None
			try:
				while not selected_version:
					try:
						selected_version = dwv._deals_with_version_func( self, *args, **kwargs )
					except ValueError:
		                                import traceback
               			                traceback.print_exc()
						pass
				print selected_version
				print func.func_name
				kwargs[ 'version_composant' ] = selected_version
				result = func( self, *args, **kwargs )
			except KeyboardException:
				raise
			except:
				import traceback
				traceback.print_exc()
				print '\t\t\tLa version n\'est pas valide'
				print '\t\t\tLe composant n\'est pas créé'
				raise
			finally:
				print red( '%s %s' % ( func.func_name, kwargs[ 'version_composant' ] ) )
				if self._print_debug: print yellow( '@%s(%s)\t|%s| -> %s' ) % ( self.filter_versions_for_type_composant_interceptor.func_name, func.func_name, 'filter_versions_for_type_composant_interceptor.wrapped', result )
				return result

		return wrapped


	##################
	# METHODES METIERS
	##################

	def create_htttp_conn( self, *args, **kwargs ):

		result = None

		if self._print_debug: print white( '\t\t\t%s(...)\t|%s| <-' ) % ( self.create_htttp_conn.func_name, 'create_htttp_conn' )

		result = HTTPConnection( self._dca_servername )

		if self._print_debug: print white( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.create_htttp_conn.func_name, 'create_htttp_conn', result )

		return result

	@process_with_httpconn_loaded_interceptor
	@process_with_env_ref_loaded_interceptor
	@process_with_type_composant_ref_loaded_interceptor
	@app_created_on_loop_interceptor
	@env_created_on_loop_interceptor
	@version_for_type_composant_created_on_loop_interceptor
	@deals_with_versions_for_type_composant_on_loop_interceptor
	def import_to_dca( self, d_applis, *args, **kwargs ):

			if self._print_debug: print blue( '\t\t\t%s(...)\t|%s| <-' ) % ( self.import_to_dca.func_name, 'import_to_dca' )

			result = None

			for app_code in d_applis.keys():

				for type_env in d_applis[ app_code ][ 'environnements' ].keys():	

					for type_composant in d_applis[ app_code ][ 'environnements' ][ type_env ][ 'composants' ]:

						for composant in d_applis[ app_code ][ 'environnements' ][ type_env ][ 'composants' ][ type_composant ]:

							self.create_composant_on_server_for_app_for_env (
								app_code			= app_code,
								type_env			= type_env,
								name_env 			= d_applis[ app_code ][ 'environnements' ][ type_env ][ 'name_env' ],
								type_composant 			= type_composant,
								name_composant			= composant[ 'name_composant' ],
								version_composant		= composant[ 'version_composant' ],
								deployment_servername_composant = composant[ 'deployment_servername_composant' ],
								desc_app_court 	      		= d_applis[ app_code ][ 'desc_app_court' ],
								desc_app_long 	      		= d_applis[ app_code ][ 'desc_app_long' ],
								desc_env 	      		= d_applis[ app_code ][ 'environnements' ][ type_env ][ 'desc_env' ],
								desc_composant        		= composant[ 'desc_composant' ],
								ip_composant          		= composant[ 'ip_composant' ],
								username_composant    		= composant[ 'username_composant' ],
							)


			if self._print_debug: print blue( '\t%s(...)\t|%s| -> %s' ) % ( self.import_to_dca.func_name, 'import_to_dca', result )
			return result


	@process_with_httpconn_loaded_interceptor
	def app_exists( self, *args, **kwargs ):

		if self._print_debug: print green( '\t\t\t%s(...)\t|%s| <-' ) % ( self.app_exists.func_name, 'app_exists' )

                self._httpconn.set_debuglevel( 0 )

		app_code = kwargs[ 'app_code' ]

		result = None

		print 'Vérification de l\'existence de l\'application %s' % ( app_code )

                get_params = urlencode ( 
			{
				u'code'.encode( 'UTF-8' ): 	u'%s'.encode( 'UTF-8' ) % ( app_code ),
				u'nom'.encode( 'UTF-8' ) : 	u''.encode( 'UTF-8' )
			}
		)

                post_params = None

                self._httpconn.request(
			'GET', 
			u'/scripts/SearchApp.php?%s'.encode('UTF-8') % ( get_params ), 
			u'%s'.encode( 'UTF-8' ) % ( post_params ), 
			self._headers 
		)
	
		resp = self._httpconn.getresponse().read()

                if not fromstring( resp ).xpath( '/Apps/App/CodeApp' ) :
			result = False
		else:
			result = True

		print result
		if self._print_debug: print green( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.app_exists.func_name, 'app_exists', result )

		return result

	@process_with_httpconn_loaded_interceptor
	@process_with_app_exists_interceptor( False )
	def create_app( self, *args, **kwargs ):

		if self._print_debug: print green( '\t\t\t%s(...)\t|%s| <-' ) % ( self.create_app.func_name, 'create_app' )

		result = None

		self._httpconn.set_debuglevel( 0 )

		app_code = kwargs[ 'app_code' ]

		print 'Création de l\'application %s' % ( app_code )

		desc_app_court = kwargs.get( 'desc_app_court', u'@TODO Décrire le nom court de %s'.encode( 'UTF-8' ) % ( app_code ) )
		desc_app_long  = kwargs.get( 'desc_app_long', u'@TODO Décrire le nom long de %s'.encode( 'UTF-8' ) % ( app_code ) ) 

		get_params = None
		post_params = urlencode( 
			{
				u'Code'.encode( 'UTF-8' ): 		u'%s'.encode( 'UTF-8' ) % ( app_code ), 
				u'NomApp'.encode( 'UTF-8' ): 		desc_app_court,
				u'NomAppCourt'.encode( 'UTF-8' ): 	desc_app_long
			} 
		)

		self._httpconn.request(
			'POST', 
			u'/carto/applications/ajouter/ajouter_exec.php'.encode('UTF-8') , 
			u'%s'.encode( 'UTF-8' ) % ( post_params ), 
			self._headers 
		)

		# Obligé de lire la réponse avant de pouvoir refaire une requête
		self._httpconn.getresponse()

		if self._print_debug: print green( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.create_app.func_name, 'create_app', result )
		return result


	@process_with_httpconn_loaded_interceptor
	def load_env_ref( self, *args, **kwargs ):

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| <-' ) % ( self.load_env_ref.func_name, 'load_env_ref' )

		result = None

		self._httpconn.set_debuglevel( 0 )

		get_params = urlencode( 
			{ 
				u'Code'.encode( 'UTF-8' ): u''.encode(' UTF-8' ) 
			} 
		)
		post_params = None

		self._httpconn.request(
			'GET', 
			u'/carto/lib/Div_AddEnvironnement.php?%s'.encode( 'UTF-8' ) % ( get_params ),
			u'%s'.encode( 'UTF-8' ) % ( post_params ), 
			self._headers 
		)

		resp = self._httpconn.getresponse().read()

		result = dict( 
				map( lambda e: ( e.text, e.attrib['value'] ), 
				HTMLParser( tree = treebuilders.getTreeBuilder( 'lxml' ) ).parse( resp ).xpath(
					'*//html:select[@id="AddEnvironnementIdTypeEnv"]/html:option', namespaces=self._d_namespaces ) 
				) 
		)

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.load_env_ref.func_name, 'load_env_ref', result )
		return result

	
	@process_with_httpconn_loaded_interceptor
	@process_with_env_ref_loaded_interceptor
	def get_id_env_for_app( self, *args, **kwargs ):
		"""
		Renvoit l'id de l'environnement (env)
		portant le nom fourni (name_env)
		pour l'app (app_code)
		indiqué ou bien lève une exception"""

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| <-' ) % ( self.get_id_env_for_app.func_name, 'get_id_env_for_app' )

		result = None

		self._httpconn.set_debuglevel( 0 )

		app_code = kwargs[ 'app_code' ]
		type_env = kwargs[ 'type_env' ]
		name_env = kwargs[ 'name_env' ]

		print '\tRécuperation id_env pour l\'environnement "%s" (%s) de %s' % ( name_env, type_env, app_code )

		get_params = urlencode(
			{ 
				u'Code'.encode( 'UTF-8' ): u'%s'.encode( 'UTF-8' ) % ( app_code )
			} 
		)
		post_params = None

		env_name_pattern='^([^\"]*)"(?P<ENV_NAME>%s)\".*$' % ( name_env )

		self._httpconn.request(
			'GET', 
			u'/carto/applications/ApplicationVoir.php?%s'.encode( 'UTF-8' ) % ( get_params ), 
			u'%s'.encode( 'UTF-8' ) % ( post_params ), 
			self._headers 
		)

		resp = self._httpconn.getresponse().read()

		result = map (
			lambda desc_env: int( desc_env.attrib['id'].replace( 'DescEnv', '' ) ),
			[ 
				desc_env for desc_env in HTMLParser( tree = treebuilders.getTreeBuilder( 'lxml' ) ).parse( resp ).xpath(
					'*//html:div[@class="DescEnv%s"]' % ( self._d_env_ref[ type_env ] ), namespaces=self._d_namespaces
				)
				if re.match( env_name_pattern, desc_env.xpath('html:h3', namespaces=self._d_namespaces )[0].text )  
			]
		)[0]

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.get_id_env_for_app.func_name, 'get_id_env_for_app', result )
		print result

		return result

        @process_with_httpconn_loaded_interceptor
        @process_with_env_ref_loaded_interceptor
	@create_app_if_needed
	@process_with_env_exists_interceptor( False )
        def create_env_for_app( self, *args, **kwargs ):
                """
		Création de l'environnement 
                pour l'environnement de type (env)
                portant le nom fourni (name_env)
                pour l'app (app_code)
		l'id d'environnement est renvoyé 
		comme résultat
		"""

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| <-' ) % ( self.create_env_for_app.func_name, 'create_env_for_app' )

		result = None

	        self._httpconn.set_debuglevel( 0 )

		app_code = kwargs[ 'app_code' ]
		type_env = kwargs[ 'type_env' ]
		name_env = kwargs[ 'name_env' ]

		print '\t\tCréation de l\'env \"%s\" (%s) de %s' % ( name_env, type_env, app_code )
		# Obtention des descriptions optionnelles
		desc_env = kwargs.get( 'desc_env', u'@TODO Décrire l\'environnement "%s" (%s)'.encode( 'UTF-8' ) % ( name_env, type_env ) )

                get_params = urlencode (
			{
				u'CodeApp'.encode( 'UTF-8' ): u'%s'.encode( 'UTF-8' ) % ( app_code ),
				u'IdTypeEnv'.encode( 'UTF-8' ): u'%s'.encode( 'UTF-8' ) % ( self._d_env_ref[ type_env ] ),
				u'Nom'.encode( 'UTF-8' ): u'%s'.encode( 'UTF-8' ) % ( name_env ),
				u'Commentaire'.encode( 'UTF-8' ): desc_env,
			}
		)
		post_params = None

                self._httpconn.request( 'GET', 
			u'/carto/lib/Exec_AddEnvironnement.php?%s'.encode( 'UTF-8' ) % ( get_params ),
			u'%s'.encode( 'UTF-8' ) % ( post_params ), 
			self._headers 
		)

                resp = self._httpconn.getresponse().read()

                result = int ( fromstring( resp ).xpath( '/retour/IdEnv' )[0].text )

		if self._print_debug: print red( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.create_env_for_app.func_name, 'create_env_for_app', result )
		print result
		return result

	
        @process_with_httpconn_loaded_interceptor
        def load_type_composant_ref( self, *args, **kwargs ):

		if self._print_debug: print cyan( '\t\t\t%s(...)\t|%s| <-' ) % ( self.load_type_composant_ref.func_name, 'load_type_composant_ref' )

		result = None

                self._httpconn.set_debuglevel( 0 )

		# Gestion des Applis
                get_params_applis = urlencode(
                        {
                               	u'TypeAjout'.encode( 'UTF-8' ): u'Serveur'.encode( 'UTF-8' ),
                               	u'TypeInstance'.encode( 'UTF-8' ): u'AppS'.encode( 'UTF-8' ),
				u'NomServeur'.encode( 'UTF-8' ): u''.encode( 'UTF-8' ),	
				u'IdServeur'.encode( 'UTF-8' ): u''.encode( 'UTF-8' )
                        }
                )

                post_params_applis = None

                self._httpconn.request(
                        'GET',
                        u'/carto/lib/Div_AddElementItem.php?%s'.encode( 'UTF-8' ) % ( get_params_applis ),
                        u'%s'.encode( 'UTF-8' ) % ( post_params_applis ),
                        self._headers
                )

                resp_applis = self._httpconn.getresponse().read()

		# Gestion des bases de données
                get_params_bdd = urlencode(
                        {
                                u'TypeAjout'.encode( 'UTF-8' ): u'Serveur'.encode( 'UTF-8' ),
                                u'TypeInstance'.encode( 'UTF-8' ): u'SGBD'.encode( 'UTF-8' ),
                                u'NomServeur'.encode( 'UTF-8' ): u''.encode( 'UTF-8' ),
                                u'IdServeur'.encode( 'UTF-8' ): u''.encode( 'UTF-8' )
                        }
                )

                post_params_bdd = None


                self._httpconn.request(
                        'GET',
                        u'/carto/lib/Div_AddElementItem.php?%s'.encode( 'UTF-8' ) % ( get_params_bdd ),
                        u'%s'.encode( 'UTF-8' ) % ( post_params_bdd ),
                        self._headers
                )


                resp_bdd = self._httpconn.getresponse().read()

		#if($GetVariable['NewType'] == "Oui" || $GetVariable['NewVersion'] == "Oui")

		result = dict(
				map( 
					lambda composant_s: 
						map( 
							# list contenant le type d'élement en premier
							# paramètre et un dictionnaire vide en second paramètre
							lambda e: 
								(
									re.match( 
										'[\s]*(.*)' , 
										e.text[ ::-1 ] 
									).group( 1 )[ ::-1 ],
									{ 'ensemble_composant': 'AppS', 'versions': None }
								), 
							# Elément option
							composant_s.xpath( 
								'html:option', 
								namespaces=self._d_namespaces
							) 
						),
					HTMLParser( tree = treebuilders.getTreeBuilder( 'lxml' ) ).parse( resp_applis ).xpath(
                                        	'*//html:select[@id="AddElementType"]', namespaces=self._d_namespaces 
                                        ),
				)[0] +
                                map(
                                        lambda composant_s:
                                                map(
                                                        # list contenant le type d'élement en premier
                                                        # paramètre et un dictionnaire vide en second paramètre
                                                        lambda e:
                                                                (
                                                                        re.match(
                                                                                '[\s]*(.*)' ,
                                                                                e.text[ ::-1 ]
                                                                        ).group( 1 )[ ::-1 ],
									{ 'ensemble_composant': 'SGBD', 'versions': None }
                                                                ),
                                                        # Elément option
                                                        composant_s.xpath(
                                                                'html:option',
                                                                namespaces=self._d_namespaces
                                                        )
                                                ),
                                        HTMLParser( tree = treebuilders.getTreeBuilder( 'lxml' ) ).parse( resp_bdd ).xpath(
                                                '*//html:select[@id="AddElementType"]', namespaces=self._d_namespaces
                                        ),
                                )[0]
			)


		if self._print_debug: print cyan( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.load_type_composant_ref.func_name, 'load_type_composant_ref', result )

		return result


	@process_with_httpconn_loaded_interceptor
	@process_with_type_composant_ref_loaded_interceptor
	def get_all_id_version_for_type_composant( self, *args, **kwargs ):

		if self._print_debug: print cyan( '\t\t\t%s(...)\t|%s| <-' ) % ( self.get_all_id_version_for_type_composant.func_name, 'get_all_id_version_for_type_composant' )

		result = None

                self._httpconn.set_debuglevel( 0 )

		# Récupération des versions disponibles des composants
		type_composant = kwargs[ 'type_composant' ]
		ensemble_composant = self._d_type_composant_ref[ type_composant ][ 'ensemble_composant' ]

                get_params = urlencode(
                        {
                                u'TypeInstance'.encode( 'UTF-8' ): u'%s'.encode(' UTF-8' ) % ( ensemble_composant ),
                                u'Type'.encode( 'UTF-8' ): u'%s'.encode(' UTF-8' ) % ( type_composant ),
                        }
                )
                post_params = None

                print "\t\t\tRécupération des versions du composant %s" % ( type_composant )

                self._httpconn.request(
                        'GET',
                        u'/carto/lib/InstanceTypeVersionComplete.php?%s'.encode( 'UTF-8' ) % ( get_params ),
                        u'%s'.encode( 'UTF-8' ) % ( post_params ),
                        self._headers
                )

                resp = self._httpconn.getresponse().read()

		result = dict (
				map(
					lambda e: (  
						e.xpath( 'VersionString' )[0].text,
						e.xpath( 'IdInstance' )[0].text, 
					),
					fromstring( resp ).xpath( '/retour/version' ) 
				)
		)

		if self._print_debug: print cyan( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.get_all_id_version_for_type_composant.func_name, 'get_all_id_version_for_type_composant', result )
		print '\t\t\t%s' % ( result )

		return result


        @process_with_httpconn_loaded_interceptor
	@process_with_version_for_type_composant_loaded_interceptor # Nouveau
	@filter_versions_for_type_composant_interceptor
        @process_with_version_for_type_composant_exists_interceptor( False )
        def create_version_for_type_composant( self,  *args, **kwargs ):

		if self._print_debug: print yellow( '\t\t\t%s(...)\t|%s| <-' ) % ( self.create_version_for_type_composant.func_name, 'create_version_for_type_composant' )

		result = 185

                self._httpconn.set_debuglevel( 9 )

		type_composant 		= kwargs[ 'type_composant' ]
		version_composant 	= kwargs[ 'version_composant' ]

                print 'Création de la version %s du type de composant %s' % ( type_composant, version_composant )

                #desc_app_court = kwargs.get( 'desc_app_court', u'@TODO Décrire le nom court de %s'.encode( 'UTF-8' ) % ( app_code ) )
                #desc_app_long  = kwargs.get( 'desc_app_long', u'@TODO Décrire le nom long de %s'.encode( 'UTF-8' ) % ( app_code ) )

                #get_params = None
                #post_params = urlencode(
                #        {
                #                u'Code'.encode( 'UTF-8' ):              u'%s'.encode( 'UTF-8' ) % ( app_code ),
                #                u'NomApp'.encode( 'UTF-8' ):            desc_app_court,
                #                u'NomAppCourt'.encode( 'UTF-8' ):       desc_app_long
                #        }
                #)

                #self._httpconn.request(
                #        'POST',
                #        u'/carto/applications/ajouter/ajouter_exec.php'.encode('UTF-8') ,
                #        u'%s'.encode( 'UTF-8' ) % ( post_params ),
                #        self._headers
                #)

                # Obligé de lire la réponse avant de pouvoir refaire une requête
                #self._httpconn.getresponse()

		if self._print_debug: print yellow( '\t\t\t%s(...)\t|%s| -> %s' ) % ( self.create_version_for_type_composant.func_name, 'create_version_for_type_composant', result )

		return result

	@process_with_httpconn_loaded_interceptor
	@create_app_if_needed
	@create_env_for_app_if_needed
	@process_with_version_for_type_composant_loaded_interceptor
	#@filter_versions_for_type_composant_interceptor
	@create_version_for_type_composant_if_needed
	def create_composant_on_server_for_app_for_env( self, *args, **kwargs ):
		"""
			Méthode création un composant sur un serveur :
			le type de composant doit être contenu dans kwargs[ 'type_composant' ]
			le nom du composant doit être contenu dans kwargs[ 'name_composant' ]
			la version du composant doit être contenu dnas kwargs[ 'version_composant' ]
			le nom du serveur de déploiement doit être contenu dans kwargs[ 'deployment_servername_composant' ]
		"""
		if self._print_debug: print cyan( '\t%s(...)\t|%s|' ) % ( self.create_composant_on_server_for_app_for_env.func_name, 'create_composant_on_server_for_app_for_env' )

	        app_code 		= kwargs[ 'app_code' ]
                type_env 		= kwargs[ 'type_env' ]
                name_env 		= kwargs[ 'name_env' ]
                type_composant          = kwargs[ 'type_composant' ]
                version_composant       = kwargs[ 'version_composant' ]
                deployment_servername_composant = kwargs[ 'deployment_servername_composant' ]

		print "create_composant_on_server_for_app_for_env"

		print version_composant

		#if not version_composant:
		#	print 'La version de composant n\'a pas été fournie'
		#elif version_composant not in self._d_type_composant[ 'versions' ]:
		#print self._d_type_composant_ref[ type_composant ][ 'versions' ].keys()

		return None
