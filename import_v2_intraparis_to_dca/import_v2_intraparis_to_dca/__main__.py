# -*- coding: iso-8859-15 -*-
import locale
import m_intraparis_descriptor
from m_intraparis_descriptor import IntraparisDescriptor
import m_import_to_dca
from m_import_to_dca import ImportToDCA

locale.setlocale(locale.LC_ALL, "")

def main():

	d_applis = {}
	intraparis_descriptor=IntraparisDescriptor.get_intraparis_descriptor('dps50', 'v2r7-intraparis.mdp', '22', [ '/home/dps50/scripts/deploiement/prod.topo', '/home/dps50/scripts/deploiement/recette.topo' ], d_applis )

	dest_dca = ImportToDCA( 'dpr-r7-suividca.mdp', 'pgoncalves', deals_with_version_funcname = 'interactive_select_version_for_type_composant' )
	#dest_dca = ImportToDCA( 'dpr-pr-suividca.mdp', 'pgoncalves', deals_with_version_funcname = 'interactive_select_version_for_type_composant' )
	#dest_dca = ImportToDCA( 'dpr-r7-suividca.mdp', 'pgoncalves', deals_with_version_funcname = 'reject_unknown_version_for_type_composant' )

	dest_dca.import_to_dca( d_applis )	

if __name__ == "__main__":
    main()
