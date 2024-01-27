$(document).ready(function () {
	$("#progressContainer").hide();
	$("#progressText").hide();

	$("#photoCaptureInput").on("change", function (event) {

		$("#progressContainer").show();
		$("#progressText").show();
		$("#progressBar").width('0%')

		const file = event.target.files[0];
		// Si il n'y a pas de fichier
		if (!file) {
			return;
		}

		// If the size of the target image is too large (e.g., greater than 10 MB),
		// you should disable this option to avoid an out - of - memory crash.
		// see: https://github.com/fengyuanchen/compressorjs
		const maxFileSize = 10 * 1024 * 1024;
		if (file.size > maxFileSize) {
			alert("La taille du fichier est trop grande.");
			return;
		}

		// Compression de l'image
		new Compressor(file, {
			quality: 0.4,
			maxWidth: 1000,
			success(result) {
				let formData = new FormData();
				formData.append("img", result, result.name);
				sendPicture(formData);
			},
			error(err) {
				console.log(err.message);
			},

		});

		$("#progressBar").width('50%')
		$("#progressNumber").text('50%')

		// Envoi de l'image au serveur
		async function sendPicture(formData) {
			$("#progressBar").width('75%');
			$("#progressNumber").text('75%')
			// On envoi l'id de la commande
			const idOrder = $("#orderPk").val();
			formData.append("orderId", idOrder);

			// On gère le csrf
			const csrfToken = $("[name=csrfmiddlewaretoken]").val();
			try {
				const response = await fetch(`/save_pictures/`, {
					method: 'POST',
					headers: {
						'X-CSRFToken': csrfToken
					},
					body: formData
				});
				// Erreur
				if (!response.ok) {
					const errorResponse = await response.json();
					let errorMessage = 'Erreur lors du traitement de la requête.';
					if (errorResponse && errorResponse.message) {
						errorMessage = errorResponse.message;
					}
					$('#pictureError').show();
					$("#pictureError").text(errorMessage);
					$("#pictureError").addClass('pictureError');
					$("#pictureError").css({"background-color": "#fef2f2", "color": "#b91c1c", "border": "1px solid #dc2626"});
					throw new Error('Erreur réseau ou réponse avec statut échoué.');
				}

				// Si tout c'est bien passé
				$("#progressBar").width('100%');
				$("#progressNumber").text('100%')
				const result = await response.json();
				$('#pictureError').show();
				$('#pictureError').removeClass();
				$("#pictureError").text('Le fichier a bien été envoyé !');
				$("#pictureError").addClass('pictureError');
				$("#pictureError").css({"background-color": "#ecfccb", "color": "#4d7c0f", "border": "1px solid #84cc16"});
				const newPictureHtml = `
				<div>
					${result.filename.name} <!-- Nom du fichier -->
					<button class="delete_picture" data-pk="${result.filename.pk}">
					</button>
					<a target="_blank" href="${result.filename.url}">
						<img class="max-h-60 max-w-full rounded-lg" src="${result.filename.url}" alt="${result.filename.name}">
					</a>
				</div>
				`;
				$("#pictureList .grid").append(newPictureHtml);
				// 	$("#pictureList").append(`
			// 	<li>
			// 		<a href="${result.filename.url}">
			// 			${result.filename.name}
			// 		</a>
			// 	</li>
			// `);
			} catch (error) {
				console.error("Il y a eu un problème avec l'opération fetch:", error);
				$("#progressContainer").hide();
				$("#progressText").hide();
			}

		}
	});

	// Ecouteur bouton Supprimer
	$(".delete_picture").click(deletePicture);
});



// Function qui supprime la photo
function deletePicture(idOrder) {
	const csrfToken = $("[name=csrfmiddlewaretoken]").val();
	let pictureId = $(this).data("pk");

	if (!pictureId) {
		pictureId = idOrder;
	}

	fetch(`/delete_picture/${pictureId}`, {
		method: 'DELETE',
		headers: {
			'X-CSRFToken': csrfToken,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			picture_id: pictureId
		})
	})
		.then(response => {
			if (!response.ok) {
				return response.text().then(text => {
					throw new Error('Erreur réseau ou réponse avec statut échoué: ' + text);
				});
			}
			return response.text();
		})
		.then(data => {
			$(".delete_canvas").closest('li').remove();
			$('#drawError').text("");
			$('#drawError').removeClass();
			location.reload();
		})
		.catch(error => {
			console.error("Il y a eu un problème avec l'opération fetch:", error);
		})
};
