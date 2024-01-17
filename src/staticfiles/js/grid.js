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
		'Paiement',
		{
			name: '',
			formatter: (_, row) => {
				return html(`<div class="flex justify-center"><a href='${row.cells[6].data}'><svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 48 48" width="25px" height="28px"><path fill="#E57373" d="M42.583,9.067l-3.651-3.65c-0.555-0.556-1.459-0.556-2.015,0l-1.718,1.72l5.664,5.664l1.72-1.718C43.139,10.526,43.139,9.625,42.583,9.067"/><path fill="#FF9800" d="M4.465 21.524H40.471999999999994V29.535H4.465z" transform="rotate(134.999 22.469 25.53)"/><path fill="#B0BEC5" d="M34.61 7.379H38.616V15.392H34.61z" transform="rotate(-45.02 36.61 11.385)"/><path fill="#FFC107" d="M6.905 35.43L5 43 12.571 41.094z"/><path fill="#37474F" d="M5.965 39.172L5 43 8.827 42.035z"/></a></div>`)
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
				return data.results.map(order => [order.IDorder, order.customer, order.label, order.status, order.created, order.payment, order.url]);
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
