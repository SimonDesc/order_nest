$(document).ready(function () {
	$(".btndelete").on("click", function (event) {
		event.preventDefault();

		if (confirm("Êtes-vous sûr de vouloir désactiver ce client ?")) {
			let id = $("#id_customer").attr("value");
			const csrfToken = $("[name=csrfmiddlewaretoken]").val();

			fetch(`/deactivate_customer/${id}`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrfToken,
					'Content-Type': 'application/json'
				},
			})
				.then(response => {
					if (!response.ok) {
						throw new Error('Erreur réseau ou réponse avec statut échoué.');
					}
					return response.text();
				})
				.then(data => {
					window.location = `${window.location.origin}/customers`;
				})
				.catch(error => {
					console.error("Il y a eu un problème avec l'opération fetch:", error);
				});
		} else {
			console.log("Action annulée par l'utilisateur.");
		}

	})
});
