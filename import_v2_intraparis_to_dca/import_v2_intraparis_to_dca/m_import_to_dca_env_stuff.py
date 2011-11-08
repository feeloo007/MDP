# -*- coding: iso-8859-15 -*-
import locale
from m_deal_with_loop import DealWithLoop
from m_debug_decorator import debug_decorator
from colors import *

locale.setlocale(locale.LC_ALL, "")


def process_with_env_ref_loaded_interceptor( func ):
        """ D�corateur valorisant la variable self_.d_env_ref pour la fonction utilis�e"""

	@debug_decorator( 'process_with_env_ref_loaded_interceptor', 'process_with_env_ref_loaded_interceptor.wrapped', '_is_ENV_in_debug', red )
        def wrapped( self, *args, **kwargs ):

                result = None

                if not self._d_env_ref:
                        # Avant traitement, cr�� le r�f�rentiel au besoin"
                        self._d_env_ref = self.load_env_ref( *args, **kwargs )

                        result = func( self, *args, **kwargs )

                        # Apr�s traitement, d�truit le r�f�rentiel
                        self._d_env_ref = None
                else:
                        # Si le r�f�rentiel existait, on ne fait que le traitement
                        # Surtout, on ne d�truit pas le r�f�rentiel
                        result = func( self, *args, **kwargs )

                return result

        return wrapped


def env_created_on_loop_interceptor( func ):

	@debug_decorator( 'env_created_on_loop_interceptor', 'env_created_on_loop_interceptor.wrapped', '_is_ENV_in_debug', red )
        def wrapped( self, *args, **kwargs ):

                result = None

                with DealWithLoop( [ self, '_is_env_on_loop', '_d_env_on_loop_created' ] ):

                        result = func( self, *args, **kwargs )
                        return result

        return wrapped


def create_env_for_app_if_needed( func ):

	@debug_decorator( 'create_env_for_app_if_needed', 'create_env_for_app_if_needed.wrapped', '_is_ENV_in_debug', red )
        def wrapped( self, *args, **kwargs ):

                result = None

                app_code = kwargs[ 'app_code' ]
                type_env = kwargs[ 'type_env' ]
                name_env = kwargs[ 'name_env' ]

                id_env = 0

                key_env = 'APP=%s,TYPE_ENV=%s,NAME_ENV=%s' %( app_code, type_env, name_env )

                if self._is_env_on_loop:
                        if key_env not in self._d_env_on_loop_created.keys():
                                id_env = self.create_env_for_app( *args, **kwargs )
                                self._d_env_on_loop_created[ key_env ] = id_env

                result = func( self, *args, **kwargs )

                return result

        return wrapped


def process_with_env_exists_interceptor( attempt ):
        """ d�corateur r�alisant la fonction func si l'existence
            de l'env est � la valeur attempt"""

	@debug_decorator( 'process_with_env_exists_interceptor', 'process_with_env_exists_interceptor.wrapper.wrapped', '_is_ENV_in_debug', red )

        def wrapper( func ):

                def wrapped( self, *args, **kwargs ):

                        result = None

                        app_code = kwargs[ 'app_code' ]
                        type_env = kwargs[ 'type_env' ]
                        name_env = kwargs[ 'name_env' ]

                        env_exists = False

                        key_env = 'APP=%s,TYPE_ENV=%s,NAME_ENV=%s' %( app_code, type_env, name_env)

                        if self._is_env_on_loop:
                                if key_env in self._d_env_on_loop_created.keys():
                                        id_env = self._d_env_on_loop_created[ key_env ]
                                        env_exists = True
                                else:
                                        try:
                                                id_env = self.get_id_env_for_app( *args, **kwargs )
                                                env_exists = True
                                                self._d_env_on_loop_created[ key_env ] = id_env
                                        except:
                                                pass
                        else:
                                try:
                                        id_env = self.get_id_env_for_app( *args, **kwargs )
                                        env_exists = True
                                except:
                                        pass

                        if env_exists == attempt:
                                result = func( self, *args, **kwargs )

                        return result

                return wrapped

        return wrapper
