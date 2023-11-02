$(document).ready(function () {

	// Fonction pour ouvrir le modal
	function openModal() {
		$("#myModal").removeClass("hidden");
		$("body").addClass("overflow-hidden");
	}

	// Fonction pour fermer le modal
	function closeModal() {
		$("#myModal").addClass("hidden");
		$("body").removeClass("overflow-hidden");
	}

	// Ajouter des écouteurs d'événements
	$("#openModalButton").on("click", openModal);
	$("#closeModalButton").on("click", closeModal);

	// Fermer le modal si on clique sur la superposition floutée
	$("#myModal .backdrop-blur-md").on("click", closeModal);

});
