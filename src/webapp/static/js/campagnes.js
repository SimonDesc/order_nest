/*
 * Onglet Campagnes : canal, public, message, aperçu en direct, test et envoi.
 * Le brouillon en cours est gardé dans le navigateur (localStorage) en cas de fausse manip.
 */
(function () {
	"use strict";

	const cfg = window.CAMPAGNES;
	const form = document.getElementById("campagne-form");
	if (!form) return;
	const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
	const $ = (sel, root = document) => root.querySelector(sel);
	const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
	const message = form.elements.message;
	const result = $("[data-result]");
	const DRAFT_KEY = "ordernest-campagne-brouillon";
	const STOP = "STOP au 36180";

	const channel = () => form.elements.channel.value;
	const audience = () => form.querySelector("[name=audience]:checked");
	// Clients retirés à la main (identifiants), et listes déjà chargées par public.
	const excluded = new Set();
	const lists = {};
	const listKey = () => `${channel()}:${audience().value}`;
	const currentList = () => lists[listKey()];
	const excludedHere = () => (currentList() || []).filter((r) => excluded.has(r.id)).length;
	const recipients = () => Number(audience().dataset[channel()] || 0) - excludedHere();

	// --- SMS : nombre de caractères et de SMS ----------------------------------------
	// Alphabet GSM 7 bits : au-delà (ê, â, œ, emoji…), un SMS ne contient plus que 70 caractères.
	const GSM = "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà";
	const GSM_EXT = "^{}\\[~]|€";

	function smsInfo(text) {
		const full = `${text} ${STOP}`;
		let units = 0;
		let unicode = false;
		for (const ch of full) {
			if (GSM.includes(ch)) units += 1;
			else if (GSM_EXT.includes(ch)) units += 2;
			else unicode = true;
		}
		const length = unicode ? [...full].length : units;
		const [single, multi] = unicode ? [70, 67] : [160, 153];
		const parts = length <= single ? 1 : Math.ceil(length / multi);
		const odd = unicode ? [...new Set([...full].filter((c) => !GSM.includes(c) && !GSM_EXT.includes(c)))] : [];
		return { length, parts, unicode, odd };
	}

	// Remplace les caractères hors alphabet GSM (ê → e, œ → oe, ’ → '…) pour revenir à 160 caractères par SMS.
	function simplify(text) {
		const map = { "œ": "oe", "Œ": "OE", "’": "'", "‘": "'", "«": "\"", "»": "\"", "“": "\"", "”": "\"", "…": "...", "–": "-", "—": "-", " ": " ", " ": " " };
		return [...text].map((ch) => {
			if (GSM.includes(ch) || GSM_EXT.includes(ch)) return ch;
			if (map[ch]) return map[ch];
			const plain = ch.normalize("NFD").replace(/[̀-ͯ]/g, "");
			return [...plain].every((c) => GSM.includes(c)) ? plain : "";
		}).join("");
	}

	// Variables ({prenom}, {nom}…) : mêmes règles que le serveur. Valeur absente → la variable
	// disparaît avec l'espace qui la précède.
	const VARIABLES = JSON.parse($("#campagne-variables").textContent || "[]");
	const SAMPLE = Object.fromEntries(VARIABLES.map((v) => [v.key, v.sample]));

	function personalize(text, values = SAMPLE) {
		return text.replace(/([ \t]?)\{(\w+)\}/g, (all, space, key) => {
			if (!(key in SAMPLE)) return all;
			const value = (values[key] || "").trim();
			return value ? space + value : "";
		});
	}

	// Même règle que le serveur : texte d'aperçu saisi, sinon le début du message sans « Bonjour {prenom}, ».
	function preheaderOf() {
		const typed = form.elements.preheader.value.trim();
		if (typed) return typed;
		let parts = (message.value || message.placeholder).split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
		if (parts.length && /^\s*(bonjour|bonsoir|cher|chère|chers|hello|salut)\b/i.test(parts[0]) && parts[0].length < 40) parts = parts.slice(1);
		const text = parts.join(" ").replace(/\s+/g, " ");
		return text.length <= 140 ? text : `${text.slice(0, 140).replace(/\s+\S*$/, "")}…`;
	}

	function unknownVariables(...texts) {
		const found = new Set();
		texts.forEach((t) => (t.match(/\{[^{}\s]{1,30}\}/g) || []).forEach((m) => {
			if (!(m.slice(1, -1) in SAMPLE)) found.add(m);
		}));
		return [...found];
	}

	// Champ où insérer une variable : le dernier utilisé (texte ou objet).
	let lastField = message;
	[message, form.elements.subject, form.elements.preheader].forEach((field) => field.addEventListener("focus", () => (lastField = field)));

	// --- Affichage selon le canal ------------------------------------------------------

	function updateChannel() {
		const ch = channel();
		$$("[data-only]").forEach((el) => (el.hidden = el.dataset.only !== ch));
		$$(".campagne-channel label").forEach((l) => l.classList.toggle("is-on", l.querySelector("input").checked));
		const test = form.elements.test_to;
		test.placeholder = test.dataset[`placeholder${ch === "email" ? "Email" : "Sms"}`];
		message.placeholder = message.dataset[`example${ch === "email" ? "Email" : "Sms"}`];
		$$(".campagne-audience").forEach((label) => {
			const input = label.querySelector("input");
			const n = Number(input.dataset[ch]);
			label.querySelector("[data-count]").textContent = n;
			label.classList.toggle("is-empty", n === 0);
		});
		update();
	}

	function update() {
		$$(".campagne-audience").forEach((l) => l.classList.toggle("is-on", l.querySelector("input").checked));
		const n = recipients();
		const go = $(".campagne-go");
		const later = channel() === "email" && form.elements.when.value === "later";
		go.textContent = n
			? `${later ? "Programmer" : "Envoyer"} à ${n} client${n > 1 ? "s" : ""}`
			: "Aucun client dans ce public";
		go.disabled = !n || (channel() === "sms" && !cfg.smsWindowOpen);
		form.elements.scheduled_at.disabled = !later;

		// Passages [à compléter] d'un modèle : l'envoi attend qu'ils soient remplacés.
		const todo = [...new Set(
			[message.value, channel() === "email" ? `${form.elements.subject.value} ${form.elements.preheader.value} ${form.elements.button_label.value}` : ""]
				.join("\n").match(/\[[^\[\]\n]{2,80}\]/g) || [],
		)];
		const todoBox = $("[data-todo]");
		todoBox.hidden = !todo.length;
		todoBox.textContent = todo.length ? `À compléter avant l'envoi : ${todo.join(" · ")}` : "";
		if (todo.length) {
			go.disabled = true;
			go.textContent = "Complétez les passages [entre crochets]";
		}

		const unknown = unknownVariables(message.value, channel() === "email" ? `${form.elements.subject.value} ${form.elements.preheader.value}` : "");
		const warn = $("[data-unknown-vars]");
		warn.hidden = !unknown.length;
		warn.textContent = unknown.length
			? `${unknown.join(", ")} n'est pas une variable connue (sans accent : ${VARIABLES.map((v) => `{${v.key}}`).join(", ")}).`
			: "";

		if (channel() === "sms") {
			const info = smsInfo(personalize(message.value || message.placeholder));
			const credits = info.parts * n;
			const limit = info.unicode ? 70 : 160;
			// Jauge : un SMS de campagne doit tenir en un seul SMS, mention STOP comprise.
			const gauge = $("[data-sms-gauge]");
			gauge.dataset.level = info.parts === 1 ? "ok" : info.parts === 2 ? "warn" : "over";
			$("[data-sms-gauge-bar]").style.width = `${Math.min(100, (info.length / limit) * 100)}%`;
			$("[data-sms-gauge-label]").textContent = info.parts === 1
				? `${info.length} / ${limit} caractères · 1 SMS par client`
				: `${info.length} caractères · ${info.parts} SMS par client`;
			let text = n ? `Environ ${credits} crédit${credits > 1 ? "s" : ""} pour ${n} clients. ` : "";
			if (info.parts === 2) text += "Le client recevra 2 SMS à la suite : raccourcissez pour tenir en un seul. ";
			if (info.parts > 2) text += `Trop long : ${info.parts} SMS à la suite, c'est pénible pour le client. Visez 160 caractères : une phrase, un lien. `;
			if (info.odd.length) text += `Caractères spéciaux (${info.odd.join(" ")}) : 70 caractères par SMS au lieu de 160. `;
			$("[data-sms-counter]").textContent = text;
			$("[data-simplify]").hidden = !info.odd.length;
			if (info.parts > 2) {
				go.disabled = true;
				go.textContent = "Message trop long pour un SMS";
			}
			$("[data-preview-sms]").textContent = `${personalize(message.value || message.placeholder)}\n${STOP}`;
		} else {
			const subject = personalize(form.elements.subject.value || form.elements.subject.placeholder);
			$("[data-preview-subject]").textContent = subject;
			$("[data-inbox-subject]").textContent = subject;
			$("[data-inbox-preheader]").textContent = personalize(preheaderOf());
			schedulePreview();
		}
		summarize();
		saveDraft();
	}

	// --- Aperçu de l'e-mail (rendu par le serveur, comme il partira) -------------------

	let previewTimer;
	function schedulePreview() {
		clearTimeout(previewTimer);
		previewTimer = setTimeout(renderPreview, 200);
	}

	async function renderPreview() {
		const frame = $(".campagne-frame");
		const body = {
			subject: form.elements.subject.value,
			preheader: form.elements.preheader.value,
			message: message.value || message.placeholder,
			button_label: form.elements.button_label.value,
			button_url: form.elements.button_url.value || "#",
		};
		try {
			const response = await fetch(frame.dataset.previewUrl, {
				method: "POST",
				headers: { "X-CSRFToken": csrf, "Content-Type": "application/json" },
				body: JSON.stringify(body),
			});
			frame.srcdoc = await response.text();
		} catch (e) {
			/* l'aperçu n'est pas essentiel */
		}
	}

	// --- Brouillon local ---------------------------------------------------------------

	const DRAFT_FIELDS = ["channel", "audience", "subject", "preheader", "message", "button_label", "button_url", "test_to"];

	// Texte du message par canal (e-mail long, SMS court).
	const texts = { email: "", sms: "" };
	let shownChannel = channel();

	function saveDraft() {
		const draft = {};
		DRAFT_FIELDS.forEach((name) => (draft[name] = form.elements[name].value));
		draft.texts = { ...texts, [channel()]: message.value };
		try { localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch (e) { /* stockage indisponible */ }
	}

	function loadDraft() {
		let draft = null;
		try { draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); } catch (e) { /* rien */ }
		if (!draft) return;
		DRAFT_FIELDS.forEach((name) => {
			const field = form.elements[name];
			if (!field || draft[name] === undefined) return;
			if (field instanceof RadioNodeList) {
				const input = $$(`[name=${name}]`, form).find((i) => i.value === draft[name]);
				if (input) input.checked = true;
			} else {
				field.value = draft[name];
			}
		});
		if (draft.texts) Object.assign(texts, draft.texts);
		shownChannel = channel();
		texts[shownChannel] = message.value;
	}

	function clearDraft() {
		try { localStorage.removeItem(DRAFT_KEY); } catch (e) { /* rien */ }
	}

	// --- Actions -----------------------------------------------------------------------

	function show(text, isError) {
		result.textContent = text;
		result.classList.toggle("relance-error", !!isError);
	}

	function payload(action) {
		const data = { action };
		["id", "channel", "audience", "subject", "preheader", "message", "button_label", "button_url", "test_to", "scheduled_at"]
			.forEach((name) => (data[name] = form.elements[name].value));
		if (!data.message.trim()) data.message = message.placeholder;
		if (data.channel === "email" && !data.subject.trim()) data.subject = form.elements.subject.placeholder;
		data.exclude = (currentList() || []).filter((r) => excluded.has(r.id)).map((r) => r.id);
		return data;
	}

	async function run(action, button) {
		const label = button.textContent;
		button.disabled = true;
		button.textContent = action === "test" ? "Envoi du test…" : "Envoi en cours…";
		show(action === "test" ? "" : "Préparation des destinataires… (jusqu'à une minute)");
		try {
			const response = await fetch(cfg.actionUrl, {
				method: "POST",
				headers: { "X-CSRFToken": csrf, "Content-Type": "application/json" },
				body: JSON.stringify(payload(action)),
			});
			const data = await response.json();
			if (data.id) form.elements.id.value = data.id;
			if (!data.ok) throw new Error(data.error || "Erreur inconnue.");
			show(data.message);
			if (action !== "test") {
				clearDraft();
				form.elements.id.value = "";
				setTimeout(() => window.location.reload(), 1800);
			}
		} catch (error) {
			show(error.message || "La connexion a échoué.", true);
		} finally {
			button.textContent = label;
			button.disabled = false;
			if (action !== "test") update();
		}
	}

	const dialog = $("#campagne-confirm");
	function confirmSend(button) {
		const n = recipients();
		const ch = channel() === "email" ? "e-mail" : "SMS";
		const later = channel() === "email" && form.elements.when.value === "later";
		if (later && !form.elements.scheduled_at.value) {
			show("Choisir la date et l'heure d'envoi.", true);
			return;
		}
		$("[data-confirm-title]", dialog).textContent = `${later ? "Programmer" : "Envoyer"} ce ${ch} à ${n} client${n > 1 ? "s" : ""} ?`;
		$("[data-confirm-text]", dialog).textContent = later
			? "La campagne pourra encore être annulée dans Brevo avant l'heure d'envoi."
			: "L'envoi ne peut pas être annulé. Pensez à vous envoyer un test avant.";
		dialog.showModal();
		dialog.onclick = (event) => {
			const value = event.target.value;
			if (!value) return;
			dialog.close();
			if (value === "ok") run(later ? "schedule" : "send", button);
		};
	}

	form.addEventListener("click", (event) => {
		const button = event.target.closest("[data-action]");
		if (button) {
			if (button.dataset.action === "test") run("test", button);
			else confirmSend(button);
			return;
		}
		if (event.target.closest("[data-simplify]")) {
			message.value = simplify(message.value || message.placeholder);
			update();
			return;
		}
		const insert = event.target.closest("[data-insert]");
		if (insert) {
			const field = lastField.closest("[hidden]") ? message : lastField;
			const start = field.selectionStart ?? field.value.length;
			const end = field.selectionEnd ?? start;
			// Une espace avant la variable si elle est collée à un mot : « Bonjour{prenom} » → « Bonjour {prenom} ».
			const before = field.value.slice(0, start);
			const text = (before && !/[\s(«'"]$/.test(before) ? " " : "") + insert.dataset.insert;
			field.setRangeText(text, start, end, "end");
			field.focus();
			update();
		}
	});

	form.addEventListener("input", update);
	form.addEventListener("change", (event) => {
		if (event.target.name === "channel") {
			// Chaque canal garde son propre texte : un e-mail ne devient pas un SMS de 7 morceaux.
			texts[shownChannel] = message.value;
			shownChannel = channel();
			message.value = texts[shownChannel] || "";
			form.elements.id.value = "";
			updateChannel();
			fillTemplates();
			templateMessage("");
		} else {
			update();
		}
	});

	// --- Résultats d'une campagne e-mail (Brevo) ---------------------------------------

	document.addEventListener("click", async (event) => {
		const button = event.target.closest("[data-stats]");
		if (!button) return;
		button.disabled = true;
		button.textContent = "Chargement…";
		try {
			const data = await (await fetch(button.dataset.stats)).json();
			if (!data.ok) throw new Error(data.error);
			const pct = (v) => (v === null ? "–" : `${v} %`);
			button.outerHTML = `<span class="campagne-stats">${data.delivered} reçus · ${data.opens} ouvertures (${pct(data.open_rate)}) · ${data.clicks} clics (${pct(data.click_rate)})${data.unsubscribed ? ` · ${data.unsubscribed} désinscrits` : ""}</span>`;
		} catch (error) {
			button.textContent = "Indisponible";
			button.title = error.message || "";
		}
	});

	// --- Crédits restants --------------------------------------------------------------

	async function loadCredits() {
		const box = $("[data-credits-url]");
		try {
			const data = await (await fetch(box.dataset.creditsUrl)).json();
			const email = data.email;
			$("[data-credit=email]", box).textContent = email
				? `E-mails Brevo : ${email.credits} restants${email.plan === "free" ? " aujourd'hui (offre gratuite : 300 par jour)" : ""}`
				: "E-mails Brevo : indisponible";
			$("[data-credit=sms]", box).textContent = data.sms !== null && data.sms !== undefined
				? `SMS : ${data.sms} crédits`
				: "SMS : indisponible";
		} catch (e) {
			box.hidden = true;
		}
	}

	// --- Modèles de message ------------------------------------------------------------

	let templates = JSON.parse($("#campagne-templates").textContent || "[]");
	const select = $("[data-template-select]");
	const deleteBtn = $("[data-template-delete]");
	const templateResult = $("[data-template-result]");
	const templateDialog = $("#campagne-template-dialog");
	const TEMPLATE_FIELDS = ["subject", "preheader", "message", "button_label", "button_url"];

	const suggestions = JSON.parse($("#campagne-suggestions").textContent || "[]");

	function fillTemplates(selectedId) {
		const own = templates.filter((t) => t.channel === channel());
		const proposed = suggestions.filter((t) => t.channel === channel());
		select.innerHTML = `<option value="">Partir d'un modèle…</option>`;
		[["Mes modèles", own], ["Modèles proposés", proposed]].forEach(([label, list]) => {
			if (!list.length) return;
			const group = document.createElement("optgroup");
			group.label = label;
			list.forEach((t) => group.append(new Option(t.name, t.id, false, String(t.id) === String(selectedId))));
			select.append(group);
		});
		deleteBtn.hidden = !currentTemplate() || currentTemplate().suggested;
	}

	function currentTemplate() {
		return templates.concat(suggestions).find((t) => String(t.id) === select.value);
	}

	function templateMessage(text, isError) {
		templateResult.textContent = text;
		templateResult.classList.toggle("relance-error", !!isError);
	}

	select.addEventListener("change", (event) => {
		event.stopPropagation();
		const t = currentTemplate();
		deleteBtn.hidden = !t || t.suggested;
		if (!t) return;
		TEMPLATE_FIELDS.forEach((name) => (form.elements[name].value = t[name] || ""));
		form.elements.id.value = "";
		if (t.audience) {
			const radio = $$("[name=audience]", form).find((r) => r.value === t.audience);
			if (radio) radio.checked = true;
			refreshAudience();
		}
		templateMessage(t.suggested
			? `Modèle « ${t.name} » chargé, avec le public conseillé. Remplacez les passages [entre crochets], puis enregistrez-le comme modèle si vous voulez le réutiliser.`
			: `Modèle « ${t.name} » chargé : modifiez-le librement, il ne change pas tant que vous ne l'enregistrez pas.`);
		update();
	});

	$("[data-template-save]").addEventListener("click", () => {
		if (!message.value.trim()) {
			templateMessage("Écrivez d'abord le message à enregistrer.", true);
			return;
		}
		const name = $("#template-name");
		name.value = (currentTemplate() && currentTemplate().name) || form.elements.subject.value.trim().slice(0, 80);
		$("[data-template-error]").textContent = "";
		templateDialog.showModal();
		name.select();
	});

	templateDialog.addEventListener("click", (event) => {
		if (event.target.value === "cancel") templateDialog.close();
	});

	templateDialog.querySelector("form").addEventListener("submit", async (event) => {
		event.preventDefault();
		const body = { name: $("#template-name").value, channel: channel() };
		TEMPLATE_FIELDS.forEach((name) => (body[name] = form.elements[name].value));
		try {
			const data = await (await fetch(cfg.templateSaveUrl, {
				method: "POST",
				headers: { "X-CSRFToken": csrf, "Content-Type": "application/json" },
				body: JSON.stringify(body),
			})).json();
			if (!data.ok) throw new Error(data.error);
			templates = templates.filter((t) => t.id !== data.template.id).concat(data.template)
				.sort((a, b) => a.name.localeCompare(b.name, "fr"));
			fillTemplates(data.template.id);
			templateDialog.close();
			templateMessage(data.message);
		} catch (error) {
			$("[data-template-error]").textContent = error.message || "La connexion a échoué.";
		}
	});

	deleteBtn.addEventListener("click", async () => {
		const t = currentTemplate();
		if (!t || !window.confirm(`Supprimer le modèle « ${t.name} » ?`)) return;
		try {
			const data = await (await fetch(cfg.templateDeleteUrl.replace("/0/", `/${t.id}/`), {
				method: "POST",
				headers: { "X-CSRFToken": csrf },
			})).json();
			if (!data.ok) throw new Error(data.error);
			templates = templates.filter((x) => x.id !== t.id);
			fillTemplates();
			templateMessage(data.message);
		} catch (error) {
			templateMessage(error.message || "La connexion a échoué.", true);
		}
	});

	// --- Aperçu : ordinateur ou mobile, hauteur ajustée au contenu ---------------------

	const frame = $(".campagne-frame");
	$$("[data-device]").forEach((button) => {
		button.addEventListener("click", () => {
			$$("[data-device]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
			frame.classList.toggle("is-mobile", button.dataset.device === "mobile");
			fitFrame();
		});
	});

	function fitFrame() {
		const doc = frame.contentDocument;
		if (doc && doc.body) frame.style.height = `${Math.max(320, doc.documentElement.scrollHeight)}px`;
	}
	frame.addEventListener("load", fitFrame);

	// --- Destinataires : qui reçoit la campagne, avec possibilité d'en retirer ---------

	const dialogRecipients = $("#campagne-recipients");
	const rowsBox = $("[data-recipients-rows]", dialogRecipients);
	const search = $("[data-recipients-search]", dialogRecipients);
	let sort = { key: "name", dir: 1 };

	async function loadList() {
		const key = listKey();
		if (!lists[key]) {
			const url = new URL(dialogRecipients.dataset.url, window.location.origin);
			url.searchParams.set("audience", audience().value);
			url.searchParams.set("channel", channel());
			const data = await (await fetch(url)).json();
			if (!data.ok) throw new Error(data.error);
			lists[key] = data.rows;
		}
		return lists[key];
	}

	function summarize() {
		const n = recipients();
		const removed = excludedHere();
		$("[data-who-summary]").textContent = `${n} client${n > 1 ? "s" : ""} recevr${n > 1 ? "ont" : "a"} ${channel() === "email" ? "cet e-mail" : "ce SMS"}`
			+ (removed ? ` · ${removed} retiré${removed > 1 ? "s" : ""} à la main` : "");
		$("[data-recipients-count]", dialogRecipients).textContent = `${n} coché${n > 1 ? "s" : ""} sur ${(currentList() || []).length}`;
	}

	function esc(text) {
		const div = document.createElement("div");
		div.textContent = text;
		return div.innerHTML;
	}

	function renderRows() {
		const q = search.value.trim().toLowerCase();
		const rows = (currentList() || [])
			.filter((r) => !q || `${r.name} ${r.contact}`.toLowerCase().includes(q))
			.sort((a, b) => {
				const x = a[sort.key], y = b[sort.key];
				return (typeof x === "number" ? x - y : String(x).localeCompare(String(y), "fr")) * sort.dir;
			});
		rowsBox.innerHTML = rows.length ? rows.map((r) => `
			<tr class="${excluded.has(r.id) ? "is-out" : ""}">
				<td class="check"><input type="checkbox" data-id="${r.id}" ${excluded.has(r.id) ? "" : "checked"} aria-label="Inclure ${esc(r.name)}"></td>
				<td class="campagne-name">${esc(r.name || "(sans nom)")}</td>
				<td>${esc(r.contact)}</td>
				<td class="num">${r.orders}</td>
				<td>${esc(r.last_order || "–")}</td>
				<td class="num">${r.spent ? `${r.spent.toLocaleString("fr-FR")} €` : "–"}</td>
				<td><a class="campagne-link" href="${r.url}" target="_blank" rel="noopener">Fiche</a></td>
			</tr>`).join("") : `<tr><td colspan="7" class="relance-empty">Aucun client${q ? " pour cette recherche" : ""}.</td></tr>`;
		const visibleIds = rows.map((r) => r.id);
		$("[data-recipients-all]", dialogRecipients).textContent =
			visibleIds.length && visibleIds.every((id) => !excluded.has(id)) ? "Tout décocher" : "Tout cocher";
		$$("th[data-sort]", dialogRecipients).forEach((th) =>
			th.setAttribute("aria-sort", th.dataset.sort === sort.key ? (sort.dir > 0 ? "ascending" : "descending") : "none"));
		summarize();
	}

	async function refreshAudience() {
		summarize();
		try {
			await loadList();
			summarize();
			update();
		} catch (e) {
			/* le résumé garde le nombre calculé par le serveur */
		}
	}

	$("[data-open-recipients]").addEventListener("click", async () => {
		const label = audience().closest("label").querySelector(".campagne-audience-label").textContent;
		$("[data-recipients-title]", dialogRecipients).textContent = `${label} · ${channel() === "email" ? "e-mail" : "SMS"}`;
		search.value = "";
		rowsBox.innerHTML = `<tr><td colspan="7" class="relance-empty">Chargement…</td></tr>`;
		dialogRecipients.showModal();
		try {
			await loadList();
			renderRows();
		} catch (error) {
			rowsBox.innerHTML = `<tr><td colspan="7" class="relance-error">${esc(error.message || "Chargement impossible.")}</td></tr>`;
		}
	});

	dialogRecipients.addEventListener("click", (event) => {
		if (event.target.value === "close" || event.target === dialogRecipients) {
			dialogRecipients.close();
			return;
		}
		const th = event.target.closest("th[data-sort]");
		if (th) {
			sort = { key: th.dataset.sort, dir: sort.key === th.dataset.sort ? -sort.dir : (th.classList.contains("num") || th.dataset.sort.endsWith("sort") ? -1 : 1) };
			renderRows();
			return;
		}
		if (event.target.closest("[data-recipients-all]")) {
			const visible = $$("input[data-id]", rowsBox).map((i) => Number(i.dataset.id));
			const allIn = visible.every((id) => !excluded.has(id));
			visible.forEach((id) => (allIn ? excluded.add(id) : excluded.delete(id)));
			renderRows();
			update();
		}
	});

	dialogRecipients.addEventListener("close", update);

	rowsBox.addEventListener("change", (event) => {
		const id = Number(event.target.dataset.id);
		if (!id) return;
		if (event.target.checked) excluded.delete(id);
		else excluded.add(id);
		event.target.closest("tr").classList.toggle("is-out", !event.target.checked);
		summarize();
		update();
	});

	search.addEventListener("input", renderRows);

	form.addEventListener("change", (event) => {
		if (event.target.name === "audience" || event.target.name === "channel") refreshAudience();
	});

	loadDraft();
	updateChannel();
	refreshAudience();
	fillTemplates();
	loadCredits();
})();
