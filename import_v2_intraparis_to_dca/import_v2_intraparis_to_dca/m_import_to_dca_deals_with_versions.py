# -*- coding: iso-8859-15 -*-
import locale
from   basen import BaseN
from colors import *
from m_lambda_color import LambdaColor

locale.setlocale(locale.LC_ALL, "")


class deals_with_version:
	_base26	= BaseN( digits='abcdefghijklmnopqrstuvwxz' )

	def __init__( self, doublet_deals_with_version_func ):
	
		self._doublet_deals_with_version_func 		= doublet_deals_with_version_func	

		self._i2dca 					= self._doublet_deals_with_version_func[ 0 ]
		self._deals_with_version_func 			= getattr( self, self._doublet_deals_with_version_func[ 1 ] )

		self._d_default_version_for_type_composant	= {}

        def __enter__( self ):
                return self

	#def __exit__( self, *exc_info ):
	#	pass

	def automatic_accept_version_for_type_composant( self, *args, **kwargs ):
                version_composant       	= kwargs[ 'version_composant' ]
		if not version_composant:
			raise KeyboardException
		return version_composant

	def interactive_select_version_for_type_composant( self, *args, **kwargs ):
                type_composant         	 	= kwargs[ 'type_composant' ]
                version_composant       	= kwargs[ 'version_composant' ]
                name_composant       		= kwargs.get ( 'name_composant' )
                deployment_servername_composant	= kwargs.get ( 'deployment_servername_composant' )
		is_default_for_type_composant 	= False

		# Vérifions si une génération de version automatique pour un composant a été demandée
		# Si oui, on renvoit la version enregistrée
		selected_version = self._d_default_version_for_type_composant.get( type_composant )

		if selected_version is not None:
			print '\t\t\tLa version %s est utilisée automatiquement pour %s.' % ( selected_version, type_composant )	
			return selected_version

		# Si nous sommes arrivé là, il n'y avait pas de version 'par défaut'
		# valide pour le type de composant
		l_versions 			= sorted ( self._i2dca._d_type_composant_ref[ type_composant ][ 'versions' ].keys() )

		# Vérifions si nous sommes dans une boucle 
		# pour deals_with_version_on_loop
		is_deals_with_versions_on_loop = self._i2dca._is_deals_with_versions_on_loop

		# Création de l'ensemble des messages
		par_defaut	=	LambdaColor( ' PAR DEFAUT pour tous les \"%s\" dans la boucle de traitement' % ( type_composant ), red ) 

		def get_name_composant_if_known():
			if not name_composant:
				return ''
			elif not deployment_servername_composant:
				return LambdaColor( ' pour \"%s\"' % ( name_composant ), green )
			else:
				return LambdaColor( ' pour \"%s\"->\"%s\"' % ( name_composant, deployment_servername_composant ), green )

		# Chaines de caractères des messages
		l_versions_exists_one_shot      	= lambda l: [ 'Utiliser%s la version %s %s' % ( get_name_composant_if_known(), e, 'du référentiel'  ) for e in l ]
		l_versions_exists_default      		= lambda l: [ 'Utiliser%s la version %s %s' % ( par_defaut, e, 'du référentiel' ) for e in l ]
		use_new_version_one_shot		= lambda v: [ 'Créer%s la nouvelle version %s' % ( get_name_composant_if_known(), e ) for e in [ v ] if e is not None ]
		use_new_version_default			= lambda v: [ 'Créer%s la nouvelle version %s' % ( par_defaut, e ) for e in [ v ] if e is not None ]
		create_new_version_one_shot		= lambda:   [ 'Créer%s une nouvelle version' % ( get_name_composant_if_known() ) ]
		create_new_version_default		= lambda:   [ 'Créer%s une nouvelle version' % ( par_defaut ) ]

		# Recherche de la chaine la plus longue en tenant compte de 
		# la potentielle boucle sur is_deals_with_versions_on_loop
		version_max_size = 0
		if is_deals_with_versions_on_loop:
			version_max_size = max(  len( e ) for e in l_versions_exists_one_shot( l_versions ) + l_versions_exists_default( l_versions ) + use_new_version_one_shot( version_composant ) + use_new_version_default( version_composant ) + create_new_version_one_shot() + create_new_version_default() )
		else:
			version_max_size = max(  len( e ) for e in l_versions_exists_one_shot( l_versions ) + use_new_version_one_shot( version_composant ) + create_new_version_one_shot() )
        	def get_select_string( i ):
                	return deals_with_version._base26.str( i )

        	def get_index_version( select_string ):
                	return deals_with_version._base26.int( select_string )

		def format_choice( select_string, selectorcolorfunc, d_suffix_desc, max_desc_size ):

			#return None

			l_select_choice_string = []

			for special_char in sorted( d_suffix_desc.keys() ):
				decorated_selected_string = lambda sc, ss: '%s%s' % ( sc, ss )
				decorated_selected_string = '%5s' % ( decorated_selected_string( special_char, select_string ) )

				decorated_desc_string = '%%-%is' % ( max_desc_size ) 
				decorated_desc_string = decorated_desc_string % ( d_suffix_desc[ special_char ] )

				l_select_choice_string.append( 
						LambdaColor( decorated_selected_string, selectorcolorfunc ).__str__()  + '/ ' + decorated_desc_string
				) 
			

			print '\t\t\t' + '\n\t\t\t'.join( [ sct for sct in l_select_choice_string  ] )

                if version_composant in l_versions:
			return version_composant
		else:
                	print '\t\t\tChoisir l\'une des options suivantes pour le type de composant %s : ' % ( type_composant ) 
			def get_d_desc( c ):
				if is_deals_with_versions_on_loop:
					return { '': c[ 0 ], '*': c[ 1 ], }
				else:
					return { '': c[ 0 ] }

			# Boucle sur les versions existantes
			for id_inter, version in enumerate( l_versions ):
				format_choice( 
					get_select_string( id_inter ), 
					green, 
					get_d_desc( [ l_versions_exists_one_shot( l_versions )[ id_inter ], l_versions_exists_default( l_versions )[ id_inter ] ] ),
					version_max_size 
				)

			# Version soumise valide. proposÃ© Ã  la crÃ©ation
			if version_composant is not None:
				 format_choice(
                                        '$', 
                                        cyan,
					get_d_desc( [ use_new_version_one_shot( version_composant )[ 0 ], use_new_version_default( version_composant )[ 0 ] ] ),
                                        version_max_size
                                )

			# Version Ã  crÃ©er
                     	format_choice(
                       		'!',
                                red,
				get_d_desc( [ create_new_version_one_shot()[ 0 ], create_new_version_default()[ 0 ] ] ),
                                version_max_size
                       	)

			# ajout de la version demandÃ©e en entrÃe et qui n'est pas dans les versions existantes

			print '\t\t\tPour sortir de l\'écran de selection sans créer de version, faire CTRL+C'
			try:
	                        selected_string = raw_input( '\t\t\tChoix : ' )
        	                if selected_string == '':
                	                raise ValueError
                       	 	if selected_string.startswith( '*' ):
                                	print '\t\t\tDéfinition d\'une version par défaut pour %s' % ( type_composant )
                                	is_default_for_type_composant = True
                                	selected_string = selected_string[ 1:: ]


				if selected_string == '$':
					print '\t\t\tDemande de création la version %s' % ( version_composant )
					return version_composant
				elif selected_string == '!':
					print '\t\t\tDemande de création d\'une nouvelle version pour %s' % ( type_composant )
					input_version = raw_input( '\t\t\tSaisir l\'identifiant de version : ' )
					if input_version == '':
						print '\t\t\tL\identifiant de version saisie n\'est pas valide'
						raise ValueError
					else:
						selected_version = input_version
						return selected_version

				# vÃ©rification de l'existence du code alphanumÃ©rique
				selected_version = l_versions[ get_index_version( selected_string ) ]
				return selected_version
			except IndexError:
                               print red( '\t\t\tChoix non valide' )
                               self.is_default_for_type_composant = False
                               raise ValueError
			except KeyError:
                               print red( '\t\t\tChoix non valide' )
                               self.is_default_for_type_composant = False
                               raise ValueError
			finally:
				if is_default_for_type_composant == True:
					if selected_version is not None:
						self._d_default_version_for_type_composant[ type_composant ] = selected_version
				print


	def reject_unknown_version_for_type_composant( self, *args, **kwargs ):
		type_composant 		= kwargs[ 'type_composant' ]
		version_composant 	= kwargs[ 'version_composant' ]

		if version_composant not in self._i2dca._d_type_composant_ref[ type_composant ][ 'versions' ].keys():
			print '\t\t\tVersion %s pour %s n\'existe pas. La version n\'est pas créée. Fin de traitement.' % ( version_composant, type_composant )
			raise KeyboardException
		else:
			return version_composant
