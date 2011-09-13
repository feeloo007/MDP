# -*- coding: iso-8859-15 -*-
import locale
import copy

locale.setlocale(locale.LC_ALL, "")


class DealWithLoop(object):
        def __init__( self, triplet_indexes ):
                # triplet_indexes est un liste contenant
                # en premier paramètre, l'objet instancié à partir de ImportToDCA
                # en second paramètre, une chaine de caractère contenant le nom du paramètre
                # définissant si la boucle est active
                # en troisieme paramètre, une chaine de caractère contenant le nom du
                # paramètre contenant les références déjà créées / récupéréés

                self._triplet_indexes           = triplet_indexes
                self._i2dca                     = triplet_indexes[0]
                self._is_on_loop_sav            = getattr( self._i2dca, self._triplet_indexes[1] )

                if self._triplet_indexes[2].__class__ == dict:
                        self._sav               = getattr( self._i2dca, self._triplet_indexes[2] ).copy()
                elif self._triplet_indexes[2].__class__ == list:
                        self._sav               = getattr( self._i2dca, self._triplet_indexes[2][ : ] )
                else:
                        self._sav               = getattr( self._i2dca, copy.copy( self._triplet_indexes[2] ) )
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


def deal_with_loop( flag_loop_name, structure_for_cache ): #, type_structure_for_cache ):

        def wrapper( func ):

                def wrapped( self, *args, **kwargs ):

                        result = None

			#if not getattr( self, flag_loop_name, False ):
			#	setattr( self, flag_loop_name, True )

			#if not getattr( self, structure_for_cache, False ):
			#	setattr( self, structure_for_cache,  )

                        with DealWithLoop( [ self, flag_loop_name, structure_for_cache ] ):

                                result = func( self, *args, **kwargs )

                                return result

                return wrapped

        return wrapper
