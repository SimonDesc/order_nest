/*
 * Visionneuse de photos : un lien <a data-lightbox="groupe" href="photo.jpg"> ouvre la
 * photo en grand dans une fenêtre au lieu d'un nouvel onglet.
 *
 * - Les liens qui partagent la même valeur de data-lightbox forment une galerie :
 *   flèches ← →, boutons précédent / suivant, balayage sur tablette.
 * - Échap, la croix ou un clic à côté de la photo ferment la visionneuse.
 * - Ctrl / Cmd + clic ou clic molette ouvrent toujours la photo dans un onglet.
 * - Le clic est capté au niveau du document : les photos ajoutées après coup
 *   (envoi d'une nouvelle photo) fonctionnent aussi.
 */
(function () {
	"use strict";

	let box, image, counter, original, prev, next;
	let gallery = [];
	let index = 0;
	let lastFocus = null;

	function build() {
		box = document.createElement("div");
		box.className = "lightbox";
		box.hidden = true;
		box.setAttribute("role", "dialog");
		box.setAttribute("aria-modal", "true");
		box.setAttribute("aria-label", "Photo");
		box.innerHTML = `
			<div class="lightbox-bar">
				<span class="lightbox-counter"></span>
				<a class="lightbox-original" target="_blank" rel="noopener">Ouvrir l'original</a>
				<button type="button" class="lightbox-close" aria-label="Fermer">&times;</button>
			</div>
			<button type="button" class="lightbox-nav lightbox-prev" aria-label="Photo précédente">&#8249;</button>
			<img class="lightbox-image" alt="">
			<button type="button" class="lightbox-nav lightbox-next" aria-label="Photo suivante">&#8250;</button>`;
		document.body.appendChild(box);

		image = box.querySelector(".lightbox-image");
		counter = box.querySelector(".lightbox-counter");
		original = box.querySelector(".lightbox-original");
		prev = box.querySelector(".lightbox-prev");
		next = box.querySelector(".lightbox-next");

		box.querySelector(".lightbox-close").addEventListener("click", close);
		prev.addEventListener("click", () => show(index - 1));
		next.addEventListener("click", () => show(index + 1));
		// Clic sur le fond (pas sur la photo ni sur un bouton) : on ferme.
		box.addEventListener("click", (event) => {
			if (event.target === box) close();
		});

		// Balayage gauche / droite sur écran tactile.
		let startX = null;
		box.addEventListener("touchstart", (e) => (startX = e.touches[0].clientX), { passive: true });
		box.addEventListener("touchend", (e) => {
			if (startX === null) return;
			const dx = e.changedTouches[0].clientX - startX;
			if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
			startX = null;
		});
	}

	function show(i) {
		if (!gallery.length) return;
		index = (i + gallery.length) % gallery.length;
		const link = gallery[index];
		const thumb = link.querySelector("img");
		image.src = link.href;
		image.alt = thumb ? thumb.alt.trim() : "";
		original.href = link.href;
		const many = gallery.length > 1;
		counter.textContent = many ? `${index + 1} / ${gallery.length}` : "";
		prev.hidden = !many;
		next.hidden = !many;
	}

	function open(link) {
		if (!box) build();
		const group = link.dataset.lightbox;
		gallery = group
			? Array.from(document.querySelectorAll(`a[data-lightbox="${CSS.escape(group)}"]`))
			: [link];
		lastFocus = document.activeElement;
		box.hidden = false;
		document.documentElement.classList.add("lightbox-open");
		show(gallery.indexOf(link));
		box.querySelector(".lightbox-close").focus();
	}

	function close() {
		box.hidden = true;
		image.removeAttribute("src");
		document.documentElement.classList.remove("lightbox-open");
		if (lastFocus) lastFocus.focus();
	}

	document.addEventListener("click", (event) => {
		const link = event.target.closest("a[data-lightbox]");
		if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) return;
		event.preventDefault();
		open(link);
	});

	document.addEventListener("keydown", (event) => {
		if (!box || box.hidden) return;
		if (event.key === "Escape") {
			event.stopPropagation();
			close();
		} else if (event.key === "ArrowLeft") {
			show(index - 1);
		} else if (event.key === "ArrowRight") {
			show(index + 1);
		}
	});
})();
