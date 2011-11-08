# -*- coding: iso-8859-15 -*-
import locale
from m_deal_with_loop import deal_with_loop
from m_debug_decorator import debug_decorator
from colors import *

locale.setlocale(locale.LC_ALL, "")


def process_with_deployment_servername_ref_loaded_interceptor( func ):
        """ Décorateur valorisant la variable self_.d_servername_ref pour la fonction utilisée"""

        @debug_decorator( 'process_with_deployment_servername_ref_loaded_interceptor', 'process_with_deployment_servername_ref_loaded_interceptor.wrapped', '_is_DEPLOYMENT_SERVERNAME_in_debug', green )
        def wrapped( self, *args, **kwargs ):

                result = None

                if not self._d_deployment_servername_ref:
                        # Avant traitement, créé le référentiel au besoin"
                        self._d_deployment_servername_ref = self.load_deployment_servername_ref( *args, **kwargs )

                        result = func( self, *args, **kwargs )

                        # Après traitement, détruit le référentiel
                        self._d_deployment_servername_ref = None
                else:
                        # Si le référentiel existait, on ne fait que le traitement
                        # Surtout, on ne détruit pas le référentiel
                        result = func( self, *args, **kwargs )

                return result

        return wrapped
