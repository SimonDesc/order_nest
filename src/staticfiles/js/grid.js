document.addEventListener("DOMContentLoaded", function () {
	const {
		html
	} = gridjs;
	const columns = [
		'ID',
		'Client',
		'Intitulé',
		'Status',

		'Création',
		{
			name: 'Modifier',
			formatter: (_, row) => {
				return html(`<a href='${row.cells[5].data}' type="button" class="blue-button div-ombre-button-edit py-2 px-6 mb-2 text-sm text-white text-gray-900 focus:outline-none rounded-xl focus:z-10 focus:ring-4 focus:ring-gray-200">
				Modifier
			</a>`)
			}
		},
	]

	const grid = new gridjs.Grid({
		columns: columns,
		search: {
			server: {
				url: (prev, keyword) => {
					const separator = prev.includes('?') ? '&' : '?';
					const searchUrl = `${prev}${separator}search=${keyword}`;
					return searchUrl;
				} 
			}
		},
		pagination: {
			limit: 20,
			server: {
				url: (prev, page, limit) => {
					const separator = prev.includes('?') ? '&' : '?';
					const paginationUrl = `${prev}${separator}page=${page}&size=${limit}`;
					return paginationUrl;
				}
			}
		},
		server: {
			url: '/get_orders/',
			then: data => {
				return data.results.map(order => [order.IDorder, order.customer, order.label, order.status, order.created, order.url]);
			},
			total: data => {
				return data.total;
			}
		},
		width: 950,
		resizable: true,

		style: {
			table: {
				border: '1px solid #162B49'
			},
			th: {
				'background-color': '#3B5B89',
				color: '#FFFFFF',
				'border-bottom': '3px solid #162B49',
				'text-align': 'center'
			},
			td: {
				'text-align': 'left'
			},
		},
		language: {
			'search': {
				'placeholder': 'Rechercher...'
			},
			'pagination': {
				'previous': 'Précédent',
				'next': 'Suivant',
				'showing': 'Affichage de',
				'to': 'à',
				'of': 'sur',
				'results': 'résultats',
				'first': 'Premier',
				'last': 'Dernier',
				'info': 'Affiche de $1 à $2 sur $3 résultats'
			},
			'loading': 'Chargement...',
			'noRecordsFound': 'Aucun enregistrement trouvé',
			'serverError': 'Erreur serveur',
			'export': {
				'csv': 'Télécharger en CSV',
				'json': 'Télécharger en JSON'
			},
			'clear': 'Effacer',
			'filter': {
				'apply': 'Appliquer',
				'cancel': 'Annuler'
			},
			'sort': {
				'asc': 'Croissant',
				'desc': 'Décroissant'
			}
		}
	  });
	grid.render(document.getElementById("wrapper"));
});
