document.addEventListener("DOMContentLoaded", function () {
	const {
		html
	} = gridjs;
	function getStatusColorClass(status) {
		if (status === 'En attente') {
			return '#FF9E2D';
		} else if (status === 'En cours') {
			return '#0060EF';
		} else if (status === 'Terminée') {
			return '#8D8D8D';
		} else if (status === 'Facturée') {
			return '#162B49';
		} else if (status === 'Annulée') {
			return '#8D8D8D';
		} else if (status === 'Urgent') {
			return '#FF4E27';
		} else {
			return 'text-slate-900';
		}
	};
	const columns = [
		'ID',
		'Client',
		'Intitulé',
		{
			name: 'Status',
			formatter: (cell) => {
				const status = cell;
				let color = getStatusColorClass(status)
				return html(`<p style="color: ${color}">${cell}</p>`)
			},
		},

		'Création',
		{
			name: 'Modifier',
			formatter: (_, row) => {
				return html(`<div style="text-align: center;">
				<a href='${row.cells[5].data}' type="button" class="blue-button div-ombre-button-edit py-2 px-6 mb-2 text-sm text-white text-gray-900 focus:outline-none rounded-xl focus:z-10 focus:ring-4 focus:ring-gray-200
				cursor-pointer transition-all   hover:-translate-y-[1px]  active:border-b-[2px]
				active:brightness-90 active:translate-y-[2px]">
				Modifier
			</a>
			</div>`)
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
		
		resizable: true,
		sort: true,
		width: '100%',
  		height: '80%',
		style: {
			container:{
				'width':'100%',
				'height':'80%'
			  },
			table: {
			},
			th: {
				'background-color': 'white',
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
