/*
 * Onglet Relances : onglets, envoi de SMS et enregistrement des relances.
 * Une ligne relancée passe en grisé avec « Relancé à l'instant ».
 */
(function () {
	"use strict";

	const config = window.RELANCES;
	const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;

	function post(url, data) {
		const body = new URLSearchParams(data);
		return fetch(url, {
			method: "POST",
			headers: { "X-CSRFToken": csrf, "Content-Type": "application/x-www-form-urlencoded" },
			body,
		}).then((r) => r.json().catch(() => ({ success: false })));
	}

	// --- Onglets ----------------------------------------------------------------------
	const tabs = document.querySelectorAll("[data-tab]");
	tabs.forEach((tab) => {
		tab.addEventListener("click", () => {
			tabs.forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
			document.querySelectorAll("[data-panel]").forEach((panel) => {
				panel.hidden = panel.dataset.panel !== tab.dataset.tab;
			});
			try { localStorage.setItem("relances-tab", tab.dataset.tab); } catch (e) { /* stockage indisponible */ }
		});
	});
	try {
		const saved = localStorage.getItem("relances-tab");
		const tab = saved && document.querySelector(`[data-tab="${saved}"]`);
		if (tab) tab.click();
	} catch (e) { /* stockage indisponible */ }

	// --- Enregistrer une relance --------------------------------------------------------
	function markDone(row, channel) {
		return post(config.followUpUrl, {
			kind: row.dataset.kind,
			customer: row.dataset.customer,
			order: row.dataset.order,
			channel,
		}).then((data) => {
			if (!data.success) throw new Error(data.error || "La relance n'a pas pu être enregistrée.");
			row.classList.add("is-done");
			row.querySelector("[data-status]").innerHTML =
				`Relancé à l'instant <small>(${channel === "sms" ? "sms" : "appel"})</small>`;
			setUndo(row, data.id);
			updateCounter(row, -1);
		});
	}

	// Compteur de l'onglet : seulement pour les lignes de la liste « à relancer ».
	function updateCounter(row, delta) {
		const counter = document.querySelector(`[data-tab="${row.dataset.kind}"] .relance-count`);
		const todoList = document.querySelector(`[data-panel="${row.dataset.kind}"] > .relance-list`);
		if (counter && row.closest(".relance-list") === todoList) {
			counter.textContent = Math.max(0, Number(counter.textContent) + delta);
		}
	}

	function setUndo(row, id) {
		const button = row.querySelector('[data-action="called"], [data-action="undo"]');
		button.dataset.action = "undo";
		button.dataset.followUp = id;
		button.textContent = "Annuler";
		button.title = "Annuler cette relance";
	}

	function undo(row, button) {
		return post(config.undoUrl.replace("/0/", `/${button.dataset.followUp}/`), {}).then((data) => {
			if (!data.success) throw new Error("La relance n'a pas pu être annulée.");
			row.classList.remove("is-done");
			row.querySelector("[data-status]").textContent = "";
			button.dataset.action = "called";
			delete button.dataset.followUp;
			button.textContent = "Appelé ✓";
			button.title = "Je l'ai appelé ou prévenu autrement";
			updateCounter(row, 1);
		});
	}

	document.addEventListener("click", (event) => {
		const button = event.target.closest("[data-action]");
		if (!button) return;
		const row = button.closest(".relance-row");
		if (button.dataset.action === "called" || button.dataset.action === "undo") {
			const action = button.dataset.action === "called" ? markDone(row, "appel") : undo(row, button);
			button.disabled = true;
			action.catch((err) => alert(err.message)).finally(() => (button.disabled = false));
		} else if (button.dataset.action === "sms") {
			openSms(row);
		}
	});

	// --- Classer un devis sans suite -------------------------------------------------------
	document.addEventListener("click", (event) => {
		const button = event.target.closest("[data-close-quote]");
		if (!button) return;
		if (!confirm("Classer ce devis sans suite ? Il passera au statut « Annulée ».")) return;
		button.disabled = true;
		post(button.dataset.closeQuote, {}).then((data) => {
			if (!data.success) {
				button.disabled = false;
				alert("Le devis n'a pas pu être classé.");
				return;
			}
			const row = button.closest(".relance-row");
			row.classList.add("is-done");
			row.querySelector("[data-status]").textContent = "Classé sans suite";
			button.remove();
		});
	});

	// --- Brevo : synchronisation à la demande ---------------------------------------------
	const syncButton = document.querySelector("[data-brevo-sync]");
	if (syncButton) {
		syncButton.addEventListener("click", () => {
			const status = document.querySelector("[data-brevo-status]");
			syncButton.disabled = true;
			syncButton.textContent = "Synchronisation…";
			post(syncButton.dataset.brevoSync, {}).then((data) => {
				status.textContent = data.success
					? `Synchronisé le ${data.date} · ${data.contacts} contacts`
					: `Échec : ${data.error || data.message || "erreur inconnue"}`;
				status.classList.toggle("relance-error", !data.success);
				syncButton.disabled = false;
				syncButton.textContent = "Synchroniser maintenant";
			});
		});
	}

	// --- SMS ------------------------------------------------------------------------------
	const dialog = document.getElementById("sms-dialog");
	const phone = document.getElementById("sms-phone");
	const text = document.getElementById("sms-text");
	const length = dialog.querySelector("[data-sms-length]");
	const error = dialog.querySelector("[data-sms-error]");
	const send = dialog.querySelector("[data-sms-send]");
	let current = null;

	const updateLength = () => (length.textContent = text.value.length);
	text.addEventListener("input", updateLength);

	function openSms(row) {
		current = row;
		dialog.querySelector("[data-sms-name]").textContent = row.dataset.name || "ce client";
		phone.value = row.dataset.phone;
		text.value = row.dataset.sms;
		error.hidden = true;
		send.disabled = false;
		send.textContent = "Envoyer le SMS";
		updateLength();
		dialog.showModal();
		text.focus();
	}

	dialog.querySelector("[data-sms-cancel]").addEventListener("click", () => dialog.close());

	send.addEventListener("click", () => {
		if (!text.value.trim() || !phone.value.trim()) return;
		if (text.value.length > 306) {
			error.textContent = "Message trop long : 306 caractères maximum.";
			error.hidden = false;
			return;
		}
		send.disabled = true;
		send.textContent = "Envoi…";
		error.hidden = true;
		const params = new URLSearchParams({ content: text.value, phone_number: phone.value });
		fetch(`${config.smsUrl}?${params}`)
			.then((r) => r.json())
			.then((data) => {
				if (!data.success) throw new Error(data.message || "Le SMS n'a pas pu être envoyé.");
				return markDone(current, "sms");
			})
			.then(() => dialog.close())
			.catch((err) => {
				error.textContent = err.message || "Le SMS n'a pas pu être envoyé.";
				error.hidden = false;
				send.disabled = false;
				send.textContent = "Réessayer";
			});
	});
})();
