# -*- coding: iso-8859-15 -*-
import locale
from colors import *

locale.setlocale(locale.LC_ALL, "")

class LambdaColor( str ):

	def __new__( cls, text, colorfunc = lambda cf: cf ):
		obj = str.__new__( cls, text )
		obj._colorfunc = colorfunc
		return obj

	@staticmethod
	def __repr_with_color_func( text, cf ):
		return ( cf( str.__str__( text ) ) )

	def activate_color( self ):
		self._colorfunc = self._colorfuncsav

	def deactivate_color( self ):
		self._colorfunc = lambda cf: cf

	def set_color_func( self, colorfunc ):
		self._colorfuncsav = self._colorfunc = colorfunc
		
	def __str__( self ):
		return LambdaColor.__repr_with_color_func( self, self._colorfunc )

	def __len__( self ):
		return str.__len__( self )
