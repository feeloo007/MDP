# -*- coding: iso-8859-15 -*-
import locale
from colors import *

locale.setlocale(locale.LC_ALL, "")

def debug_decorator( real_name_func, real_stack, is_in_debug, color = white ):

	def wrapper( func ):

		def wrapped( self, *args, **kwargs ):

			result = None

			with_exception = False


			if not getattr( self, is_in_debug, False ):

				result = func( self, *args, **kwargs )

			else:

				try:

					print color( '@%s(%s)\t|%s| <-' ) % ( real_name_func, func.func_name, real_stack )
					#print color( '%s' ) % ( kwargs )

					result = func( self, *args, **kwargs )

				except:

					with_exception = True
					raise

				finally:

					if not with_exception:

						print color( '@%s(%s)\t|%s| -> %s' ) % ( real_name_func, func.func_name, real_stack, result )

					else:
						
						print color( '@%s(%s)\t|%s| EXCEPTION' ) % ( real_name_func, func.func_name, real_stack )

			return result

		return wrapped

	return wrapper
