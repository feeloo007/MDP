# -*- coding: iso-8859-15 -*-
import sys

l_modules_to_load = 	[ 
				'import_v2_intraparis_to_dca.%s' % ( m ) 
				for m in 
					'm_debug_decorator',
					'm_deal_with_loop',
					'__main__',
					'm_intraparis_descriptor',
				 	'm_lambda_color',
					'm_import_to_dca_deals_with_versions',
					'm_import_to_dca_appcode_stuff',
					'm_import_to_dca_env_stuff',
					'm_import_to_dca_type_composant_stuff',
					'm_import_to_dca_version_for_type_composant_stuff',
					'm_import_to_dca',
					'm_import_to_dca_deployment_servername_stuff',
			]

for s_m in l_modules_to_load:
	m = sys.modules.get( s_m )
	if not m:
		m = __import__( s_m )
	else:
		reload( m )

from m_deal_with_loop import *
from m_debug_decorator import *
from __main__ import main
from m_intraparis_descriptor import *
from m_import_to_dca import *
from m_import_to_dca_appcode_stuff import *
from m_lambda_color import *
from m_import_to_dca_deals_with_versions import *
from m_import_to_dca_deployment_servername_stuff import *
