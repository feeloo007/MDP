# -*- coding: iso-8859-15 -*-
import locale
from m_deal_with_loop import deal_with_loop
from m_debug_decorator import debug_decorator
from colors import *

locale.setlocale(locale.LC_ALL, "")


#def app_created_on_loop_interceptor( func ):
#
#	@debug_decorator( 'app_created_on_loop_interceptor', 'app_created_on_loop_interceptor.wrapped', '_is_APP_in_debug', green )
#	def wrapped( self, *args, **kwargs ):
#	
#                result = None
#
#                with DealWithLoop( [ self, '_is_app_on_loop', '_d_app_on_loop_created' ] ):
#
#                	result = func( self, *args, **kwargs )
#                       return result
#
#	return wrapped

def app_created_on_loop_interceptor( func ):

        @debug_decorator( 'app_created_on_loop_interceptor', 'app_created_on_loop_interceptor.wrapped', '_is_APP_in_debug', green )
	@deal_with_loop( '_is_app_on_loop', '_d_app_on_loop_created' )
        def wrapped( self, *args, **kwargs ):

		return func( self, *args, **kwargs )

        return wrapped



def create_app_if_needed( func ):

	@debug_decorator( 'create_app_if_needed', 'create_app_if_needed.wrapped', '_is_APP_in_debug', green )
        def wrapped( self, *args, **kwargs ):

                result = None

                app_code = kwargs[ 'app_code' ]

                if self._is_app_on_loop:
                	if app_code not in self._d_app_on_loop_created.keys():
                        	self.create_app( *args, **kwargs )
                                self._d_app_on_loop_created[ app_code ] = app_code

                result = func( self, *args, **kwargs )

                return result

       	return wrapped


def process_with_app_exists_interceptor( attempt ):
        """ d?corateur r?alisant la fonction func si l'existence
            de l'env est ? la valeur attempt"""

	@debug_decorator( 'process_with_app_exists_interceptor', 'process_with_app_exists_interceptor.wrapped', '_is_APP_in_debug', green )
        def wrapper( func ):

                def wrapped( self, *args, **kwargs ):

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

                        return result

                return wrapped

        return wrapper
