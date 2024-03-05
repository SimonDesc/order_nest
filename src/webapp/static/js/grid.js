// Gestion des onglets
function openTab(evt, tabName) {
	var i, tabcontent, tablinks;

	// Cache les onglets
	tabcontent = document.getElementsByClassName("tab-content");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].classList.add("hidden");
	}

	// Enlève la classe "active" de tous les éléments avec la classe "tablink"
	tablinks = document.querySelectorAll(".flex ul li a");
	tablinks.forEach(function (link) {
		link.classList.remove("blue-color-text", "border-gray-300", "text-white");
		link.classList.add("grey-color");
	});

	// Affiche le contenu de l'onglet courant et ajoute la classe "active"
	document.getElementById(tabName).classList.remove("hidden");
	evt.currentTarget.classList.remove("grey-color");
	evt.currentTarget.classList.add("border-b-2", "blue-color-text", "border-gray-300", "text-white");
}

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
		{ id: 'ID', name: 'ID' },
		{ id: 'Client', name: 'Client' },
		{ id: 'Intitule', name: 'Intitulé' },
		{
			id: 'Status',
			name: 'Status',
			formatter: (cell) => {
				const status = cell;
				let color = getStatusColorClass(status)
				return html(`<p style="color: ${color}">${cell}</p>`)
			},
		},

		{
			id: 'Creation',
			name: 'Création',
			formatter: (cell) => {
				const date = new Date(cell);
				const formattedDate = date.toLocaleDateString('fr-FR');
				return html(`<span>${formattedDate}</span>`);
			},
		},
		{ id: 'Paiement', name: 'Paiement' },
		{
			id: 'Edit',
			name: '',
			formatter: (_, row) => {
				return html(`
				<div class="flex justify-center"><a href='${row.cells[6].data}'>
				<img width="25" height="20" src="/static/img/edit.svg">
				`)
			}
		},
	]

	function createStatusTable(statusFilter) {
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
						// const paginationUrl = `${prev}${separator}page=${page}&size=${limit}`;
						const statusFilter2 = statusFilter.join(',');
        				const paginationUrl = `${prev}${separator}page=${page}&size=${limit}&status=${statusFilter2}`;
						return paginationUrl;
					}
				}
			},
			server: {
				url: '/get_orders/',
				then: data => data.results
					.filter(order => statusFilter.some(status => order.status === status))
					.map(order => [order.IDorder, order.customer, order.label, order.status, order.created, order.payment, order.url]),
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
		});
	}

	const gridEncours = createStatusTable(['En cours', 'Urgent', 'En attente']);
	gridEncours.render(document.getElementById("wrapper"));

	const gridTermines = createStatusTable(['Terminée', 'Annulée']);
	gridTermines.render(document.getElementById("wrapperEnCours"));

	const gridFacture = createStatusTable(['Facturée']);
	gridFacture.render(document.getElementById("wrapperFacture"));




	// Pour afficher l'onglet par défaut au chargement
	document.getElementById("default-tab").click();


});
