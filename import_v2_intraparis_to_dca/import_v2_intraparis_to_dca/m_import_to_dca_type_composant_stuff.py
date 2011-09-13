# -*- coding: iso-8859-15 -*-
import locale
from m_deal_with_loop import DealWithLoop
from m_debug_decorator import debug_decorator
from colors import *

locale.setlocale(locale.LC_ALL, "")


def process_with_type_composant_ref_loaded_interceptor( func ):
        """ D�corateur valorisant la variable self_._d_type_composant_ref pour la fonction utilis�e"""

	@debug_decorator( 'process_with_type_composant_ref_loaded_interceptor', 'process_with_type_composant_ref_loaded_interceptor.wrapped', '_is_TYPE_COMPOSANT_in_debug', blue )
        def wrapped( self, *args, **kwargs ):

                result = None

                if not self._d_type_composant_ref:
                        # Avant traitement, cr�� le r�f�rentiel au besoin
                        self._d_type_composant_ref = self.load_type_composant_ref( *args, **kwargs )

                        result = func( self, *args, **kwargs)

                        # Apr�s traitement, d�truit le r�f�rentiel
                        self._d_type_composant_ref = None
                else:
                        # Si le r�f�rentiel existait, on ne fait que le traitement
                        # Surtout, on ne d�truit pas le r�f�rentiel
                        result = func( self, *args, **kwargs)

                return result

        return wrapped
