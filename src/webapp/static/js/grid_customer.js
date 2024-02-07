document.addEventListener("DOMContentLoaded", function () {
	const {
		html
	} = gridjs;

	const columns = [
		{ id: 'Nom', name: 'Nom' },
		{ id: 'Prenom', name: 'Prénom' },
		{ id: 'Telephone', name: 'Téléphone' },
		{ id: 'Mail', name: 'E-mail' },
		{
			id: 'Edit',
			name: '',
			formatter: (_, row) => {
				return html(`
				<div class="flex justify-center"><a href='${row.cells[4].data}'>
				<img width="25" height="20" src="/static/img/edit.svg">
				`)
			}
		},
	]


	return new gridjs.Grid({
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
			url: '/get_customers/',
			then: data => {
				return data.results.map(customer => [customer.last_name, customer.first_name, customer.phone_number, customer.mail, customer.url]);
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
			container: {
				'width': '100%',
				'height': '80%'
			},
			table: {
			},
			th: {
				'background-color': '#f3f4f6',
				'color': '#111827',
				'text-align': 'center',
				'padding': '10px',
				'border-bottom': '2px solid #e5e7eb',
			},
			td: {
				'text-align': 'left',
				'padding': '10px',
				'border-bottom': '1px solid #e5e7eb',
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
	}).render(document.getElementById("wrapperCustomer"));



});
