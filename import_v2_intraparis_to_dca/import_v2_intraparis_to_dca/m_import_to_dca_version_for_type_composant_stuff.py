# -*- coding: iso-8859-15 -*-
import locale
from m_deal_with_loop import DealWithLoop
from m_debug_decorator import debug_decorator
from colors import *

locale.setlocale(locale.LC_ALL, "")



def process_with_version_for_type_composant_loaded_interceptor( func ):
        """ Décorateur valorisant la variable self_._d_type_composant_ref [ type_composant ]
            type_composant étant passé par la variables kwargs"""

	@debug_decorator( 'process_with_version_for_type_composant_loaded_interceptor', 'process_with_version_for_type_composant_loaded_interceptor.wrapped', '_is_VERSION_FOR_TYPE_COMPOSANT_in_debug', yellow )
        def wrapped( self, *args, **kwargs ):

                result = None

                type_composant = kwargs[ 'type_composant' ]

                if not self._d_type_composant_ref[ type_composant ][ 'versions' ]:
                        print '\t\tRécupération de self._d_type_composant_ref[ %s ]' % ( type_composant )
                        self._d_type_composant_ref[ type_composant ][ 'versions' ] = self.get_all_id_version_for_type_composant( *args, **kwargs )
                        result = func( self, *args, **kwargs)
                else:
                        result = func( self, *args, **kwargs)

                return result

        return wrapped


def version_for_type_composant_created_on_loop_interceptor( func ):

	@debug_decorator( 'version_for_type_composant_created_on_loop_interceptor', 'version_for_type_composant_created_on_loop_interceptor.wrapped', '_is_VERSION_FOR_TYPE_COMPOSANT_in_debug', yellow )
        def wrapped( self, *args, **kwargs ):

                result = None

                with DealWithLoop( [ self, '_is_version_on_loop', '_d_version_on_loop_created' ] ):

                        result = func( self, *args, **kwargs )

                        return result

        return wrapped


def create_version_for_type_composant_if_needed( func ):

	@debug_decorator( 'create_version_for_type_composant_if_needed', 'create_version_for_type_composant_if_needed.wrapped', '_is_VERSION_FOR_TYPE_COMPOSANT_in_debug', yellow )
        def wrapped( self, *args, **kwargs ):

                result = None

                type_composant          = kwargs[ 'type_composant' ]
                version_composant       = kwargs[ 'version_composant' ]
                key_version_composant   = 'TYPE_COMPOSANT=%s,VERSION_COMPOSANT=%s' % ( type_composant, version_composant )

                id_version = 0

                if self._is_version_on_loop:
                        if key_version_composant not in self._d_version_on_loop_created.keys():
                                id_version = self.create_version_for_type_composant( *args, **kwargs )
                		self._d_version_on_loop_created[ key_version_composant ] = id_version
			else:
				id_version = self._d_version_on_loop_created[ key_version_composant ]
		else:
			id_version = self.create_version_for_type_composant( *args, **kwargs )

                result = func( self, *args, **kwargs )

                return result

        return wrapped


def process_with_version_for_type_composant_exists_interceptor( attempt ):
        """ décorateur réalisant la fonction func si l'existence
            de la version est à la valeur attempt"""

	@debug_decorator( 'process_with_version_for_type_composant_exists_interceptor', 'process_with_version_for_type_composant_exists_interceptor.wrapper.wrapped', '_is_VERSION_FOR_TYPE_COMPOSANT_in_debug', yellow )
        def wrapper( func ):

                def wrapped( self, *args, **kwargs ):

                        result = None

                        type_composant          = kwargs[ 'type_composant' ]
                        version_composant       = kwargs[ 'version_composant' ]
                        key_version_composant   = 'TYPE_COMPOSANT=%s,VERSION_COMPOSANT=%s' % ( type_composant, version_composant )

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

                        return result

                return wrapped

        return wrapper
