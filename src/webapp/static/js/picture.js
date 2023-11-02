$(document).ready(function () {
	$("#photoCaptureInput").on("change", function (event) {
		const file = event.target.files[0];
		let formData = new FormData();
		formData.append("img", file);
		const idOrder = $("#orderPk").val();
		formData.append("orderId", idOrder);
		const csrfToken = $("[name=csrfmiddlewaretoken]").val();

		if (file) {
			fetch(`/save_pictures/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrfToken
				},
				body: formData
			})
				.then(response => {
					if (!response.ok) {
						throw new Error('Erreur réseau ou réponse avec statut échoué.');
					}
					console.log("reponse + ",  response)
					return response.text()
				})
				.then(file => {
					console.log("file + ", file)
					// location.reload();
				})
				.catch(error => {
					console.error("Il y a eu un problème avec l'opération fetch:", error);
				});
		}
	});

});
