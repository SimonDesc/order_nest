/*
 * Graphiques de la page d'accueil, en SVG sans dépendance :
 *  - une courbe de tendance (12 mois) sous chaque indicateur ;
 *  - l'activité mensuelle, année en cours vs année précédente.
 */
(function () {
	"use strict";

	const SVG_NS = "http://www.w3.org/2000/svg";
	const intFmt = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
	const eurFmt = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

	const fmt = (value, format) => (format === "eur" ? eurFmt.format(value) : intFmt.format(value));
	const compactEur = (value) => (value >= 1000 ? intFmt.format(value / 1000) + " k€" : intFmt.format(value) + " €");

	function readJson(id) {
		const el = document.getElementById(id);
		return el ? JSON.parse(el.textContent) : null;
	}

	function el(name, attrs, parent) {
		const node = document.createElementNS(SVG_NS, name);
		for (const key in attrs) node.setAttribute(key, attrs[key]);
		if (parent) parent.appendChild(node);
		return node;
	}

	function cssVar(node, name) {
		return getComputedStyle(node).getPropertyValue(name).trim();
	}

	// Graduations « rondes » : 0, 10, 20, 30… ou 0, 5 000, 10 000…
	function niceScale(max, count) {
		if (max <= 0) return { max: 1, ticks: [0, 1] };
		const raw = max / count;
		const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
		const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw);
		const top = Math.ceil(max / step) * step;
		const ticks = [];
		for (let v = 0; v <= top + step / 2; v += step) ticks.push(v);
		return { max: top, ticks };
	}

	// Barre arrondie (4 px) côté valeur, carrée sur la ligne de base.
	function barPath(x, y, w, h) {
		if (h <= 0) return "";
		const r = Math.min(4, w / 2, h);
		return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
	}

	function makeTooltip(container) {
		const tip = document.createElement("div");
		tip.className = "viz-tooltip";
		tip.setAttribute("role", "status");
		container.appendChild(tip);
		return {
			show(html, x, y) {
				tip.innerHTML = html;
				tip.classList.add("visible");
				// On garde l'infobulle dans la carte.
				const half = tip.offsetWidth / 2;
				const left = Math.max(half, Math.min(container.clientWidth - half, x));
				tip.style.left = left + "px";
				tip.style.top = y + "px";
			},
			hide() {
				tip.classList.remove("visible");
			},
		};
	}

	function onResize(node, draw) {
		let width = 0;
		const run = () => {
			if (node.clientWidth && node.clientWidth !== width) {
				width = node.clientWidth;
				draw();
			}
		};
		if ("ResizeObserver" in window) new ResizeObserver(run).observe(node);
		else window.addEventListener("resize", run);
		run();
	}

	/* ---------- Courbes de tendance ---------- */

	function drawSparkline(node, points, format) {
		const tooltip = makeTooltip(node);
		let svg;

		function draw() {
			if (svg) svg.remove();
			const w = node.clientWidth;
			const h = node.clientHeight - parseFloat(getComputedStyle(node).paddingTop);
			const pad = 5;
			const max = Math.max(...points.map((p) => p.value), 1);
			const x = (i) => pad + (i * (w - pad * 2)) / (points.length - 1);
			const y = (v) => pad + (1 - v / max) * (h - pad * 2);
			const last = points.length - 1;

			svg = el("svg", { viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: "none" });
			svg.style.height = h + "px";
			node.insertBefore(svg, node.firstChild);

			const spark = cssVar(node, "--viz-spark");
			const accent = cssVar(node, "--viz-current");
			const done = points.slice(0, last).map((p, i) => `${x(i)},${y(p.value)}`);

			el("path", {
				d: `M${x(0)},${h}L${done.join("L")}L${x(last)},${y(points[last].value)}L${x(last)},${h}Z`,
				fill: spark, "fill-opacity": 0.14, stroke: "none",
			}, svg);
			el("polyline", {
				points: done.join(" "), fill: "none", stroke: spark,
				"stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round",
			}, svg);
			// Le mois en cours n'est pas fini : segment en pointillé.
			el("line", {
				x1: x(last - 1), y1: y(points[last - 1].value), x2: x(last), y2: y(points[last].value),
				stroke: spark, "stroke-width": 2, "stroke-dasharray": "2 3", "stroke-linecap": "round",
			}, svg);
			el("circle", { cx: x(last), cy: y(points[last].value), r: 4, fill: accent, stroke: "#fff", "stroke-width": 2 }, svg);

			const hover = el("circle", { r: 4, fill: accent, stroke: "#fff", "stroke-width": 2, visibility: "hidden" }, svg);
			const hit = el("rect", { x: 0, y: 0, width: w, height: h, fill: "transparent" }, svg);

			hit.addEventListener("pointermove", (event) => {
				const rect = svg.getBoundingClientRect();
				const i = Math.max(0, Math.min(last, Math.round(((event.clientX - rect.left - pad) / (w - pad * 2)) * last)));
				const p = points[i];
				hover.setAttribute("cx", x(i));
				hover.setAttribute("cy", y(p.value));
				hover.setAttribute("visibility", "visible");
				const top = y(p.value) + parseFloat(getComputedStyle(node).paddingTop);
				tooltip.show(
					`<div class="tt-title">${p.label}${i === last ? " (en cours)" : ""}</div>${fmt(p.value, format)}`,
					x(i), top
				);
			});
			hit.addEventListener("pointerleave", () => {
				hover.setAttribute("visibility", "hidden");
				tooltip.hide();
			});
		}

		onResize(node, draw);
	}

	/* ---------- Activité : une courbe par année ---------- */

	const METRICS = {
		orders: { format: "int", name: "Commandes" },
		revenue: { format: "eur", name: "Chiffre d'affaires" },
		customers: { format: "int", name: "Nouveaux clients" },
	};
	const MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
	const MAX_YEARS = 3;

	// La couleur suit l'année (année % 3), pas son rang : trois années qui se suivent
	// ont toujours trois couleurs différentes, et une année garde sa couleur d'une
	// année sur l'autre. Palette validée (daltonisme compris).
	const YEAR_COLORS = ["#eb6834", "#2a78d6", "#1baf7a"];
	const yearColor = (year) => YEAR_COLORS[year % 3];

	function drawYears(node, history, legend) {
		const tooltip = makeTooltip(node);
		let metric = "orders";
		let svg;

		// { 2024: [12 mois], ... } ; null pour les mois sans donnée (avant la première
		// commande, ou à venir).
		const byYear = {};
		history.forEach((h) => {
			byYear[h.year] = byYear[h.year] || { months: new Array(12).fill(null), partial: null };
			byYear[h.year].months[h.month - 1] = h;
			if (h.partial) byYear[h.year].partial = h.month - 1;
		});
		const years = Object.keys(byYear).map(Number).sort().slice(-MAX_YEARS);
		const current = years[years.length - 1];

		if (legend) {
			legend.innerHTML = years
				.map((y) => `<span><i class="legend-swatch" style="background:${yearColor(y)}"></i>${y}${y === current ? " (en cours)" : ""}</span>`)
				.join("");
		}

		function draw() {
			if (svg) svg.remove();
			const w = node.clientWidth;
			const h = node.clientHeight;
			const isEur = metric === "revenue";
			const label = isEur ? compactEur : (v) => intFmt.format(v);
			const value = (y, i) => {
				const point = byYear[y].months[i];
				return point ? point[metric] : null;
			};

			const all = [];
			years.forEach((y) => byYear[y].months.forEach((_, i) => value(y, i) !== null && all.push(value(y, i))));
			const scale = niceScale(Math.max(...all, 1), 4);
			const m = { top: 12, right: 46, bottom: 24, left: isEur ? 44 : 30 };
			const plotW = w - m.left - m.right;
			const plotH = h - m.top - m.bottom;
			const step = plotW / 11;
			const x = (i) => m.left + step * i;
			const y = (v) => m.top + plotH * (1 - v / scale.max);

			svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": `${METRICS[metric].name} par mois, ${years.join(", ")}` });
			node.insertBefore(svg, node.firstChild);

			const grid = cssVar(node, "--viz-grid");
			const muted = cssVar(document.documentElement, "--muted") || "#6b7280";
			const ink = cssVar(document.documentElement, "--ink") || "#1f2a33";

			scale.ticks.forEach((t) => {
				el("line", { x1: m.left, x2: w - m.right + 6, y1: y(t), y2: y(t), stroke: grid, "stroke-width": 1 }, svg);
				const text = el("text", { x: m.left - 8, y: y(t), "text-anchor": "end", "dominant-baseline": "middle", fill: muted, "font-size": 11 }, svg);
				text.textContent = label(t);
			});
			MONTHS.forEach((name, i) => {
				const text = el("text", { x: x(i), y: h - 6, "text-anchor": "middle", fill: muted, "font-size": 11 }, svg);
				text.textContent = step < 34 ? name.charAt(0) : name;
			});

			const cross = el("line", { y1: m.top, y2: m.top + plotH, stroke: grid, "stroke-width": 1, visibility: "hidden" }, svg);

			// Les années passées d'abord, l'année en cours par-dessus.
			const ends = [];
			years.forEach((yr) => {
				const color = yearColor(yr);
				const isCurrent = yr === current;
				const partial = byYear[yr].partial;
				const pts = [];
				for (let i = 0; i < 12; i++) {
					const v = value(yr, i);
					if (v !== null) pts.push([i, v]);
				}
				if (!pts.length) return;
				const solid = pts.filter(([i]) => i !== partial);
				el("polyline", {
					points: solid.map(([i, v]) => `${x(i)},${y(v)}`).join(" "),
					fill: "none", stroke: color, "stroke-width": isCurrent ? 2.5 : 2,
					"stroke-linejoin": "round", "stroke-linecap": "round",
				}, svg);
				// Mois en cours, pas terminé : segment en pointillé et point creux.
				if (partial !== null && value(yr, partial) !== null && partial > 0 && value(yr, partial - 1) !== null) {
					el("line", {
						x1: x(partial - 1), y1: y(value(yr, partial - 1)), x2: x(partial), y2: y(value(yr, partial)),
						stroke: color, "stroke-width": 2, "stroke-dasharray": "2 4", "stroke-linecap": "round",
					}, svg);
				}
				if (isCurrent) {
					solid.forEach(([i, v]) => el("circle", { cx: x(i), cy: y(v), r: 3.5, fill: color, stroke: "#fff", "stroke-width": 2 }, svg));
				}
				if (partial !== null && value(yr, partial) !== null) {
					el("circle", { cx: x(partial), cy: y(value(yr, partial)), r: 4, fill: "#fff", stroke: color, "stroke-width": 2 }, svg);
				}
				const [lastI, lastV] = solid.length ? solid[solid.length - 1] : pts[pts.length - 1];
				ends.push({ yr, x: x(lastI), y: y(lastV), color, isCurrent });
			});

			// Libellé de l'année au bout de chaque courbe ; écartés s'ils se chevauchent.
			ends.sort((a, b) => a.y - b.y);
			for (let i = 1; i < ends.length; i++) {
				if (ends[i].y - ends[i - 1].y < 13) ends[i].y = ends[i - 1].y + 13;
			}
			ends.forEach((e) => {
				const text = el("text", {
					x: e.x + 8, y: e.y, "dominant-baseline": "middle", "font-size": 11,
					"font-weight": e.isCurrent ? 700 : 500, fill: ink,
				}, svg);
				text.textContent = e.yr;
			});

			const markers = years.map((yr) => el("circle", { r: 4, fill: yearColor(yr), stroke: "#fff", "stroke-width": 2, visibility: "hidden" }, svg));

			// Survol : un mois entier, toutes les années.
			for (let i = 0; i < 12; i++) {
				const hit = el("rect", { x: x(i) - step / 2, y: m.top, width: step, height: plotH, fill: "transparent" }, svg);
				hit.addEventListener("pointerenter", () => {
					cross.setAttribute("x1", x(i));
					cross.setAttribute("x2", x(i));
					cross.setAttribute("visibility", "visible");
					let top = m.top + plotH;
					const rows = years.slice().reverse().map((yr) => {
						const v = value(yr, i);
						const marker = markers[years.indexOf(yr)];
						if (v === null) {
							marker.setAttribute("visibility", "hidden");
							return `<div class="tt-row"><i class="legend-swatch" style="background:${yearColor(yr)}"></i>${yr}<b>–</b></div>`;
						}
						marker.setAttribute("cx", x(i));
						marker.setAttribute("cy", y(v));
						marker.setAttribute("visibility", "visible");
						top = Math.min(top, y(v));
						const note = byYear[yr].partial === i ? " <small>(en cours)</small>" : "";
						return `<div class="tt-row"><i class="legend-swatch" style="background:${yearColor(yr)}"></i>${yr}${note}<b>${fmt(v, METRICS[metric].format)}</b></div>`;
					});
					tooltip.show(`<div class="tt-title">${MONTHS[i]} · ${METRICS[metric].name}</div>${rows.join("")}`, x(i), Math.min(top, m.top + plotH * 0.55));
				});
				hit.addEventListener("pointerleave", () => {
					cross.setAttribute("visibility", "hidden");
					markers.forEach((mk) => mk.setAttribute("visibility", "hidden"));
					tooltip.hide();
				});
			}
		}

		onResize(node, draw);
		return (next) => {
			metric = next;
			draw();
		};
	}

	/* ---------- Tendances : barres empilées par période ---------- */

	const QUARTERS = ["T1", "T2", "T3", "T4"];

	// Regroupe les mois en périodes (mois, trimestre, année) et somme chaque série.
	function groupPeriods(months, period) {
		const groups = [];
		const index = {};
		months.forEach((mo, i) => {
			let key, label, short;
			if (period === "year") {
				key = String(mo.year); label = key; short = key;
			} else if (period === "quarter") {
				const q = Math.floor((mo.month - 1) / 3);
				key = `${mo.year}-${q}`; label = `${QUARTERS[q]} ${mo.year}`; short = QUARTERS[q];
			} else {
				key = mo.key; label = `${MONTHS[mo.month - 1]} ${mo.year}`; short = MONTHS[mo.month - 1];
			}
			if (!(key in index)) {
				index[key] = groups.length;
				groups.push({ key, label, short, year: mo.year, months: [] });
			}
			groups[index[key]].months.push(i);
		});
		// La dernière période contient le mois en cours : elle n'est pas terminée.
		groups[groups.length - 1].partial = true;
		return groups;
	}

	function drawTrend(node, legend, chart, months) {
		const tooltip = makeTooltip(node);
		let period = "quarter";
		let mode = "count";
		let svg;

		legend.innerHTML = chart.series
			.map((s) => `<span><i class="legend-swatch" style="background:${s.color}"></i>${s.label}</span>`)
			.join("");

		function draw() {
			if (!node.clientWidth) return; // vue masquée : dessinée quand elle s'affiche
			if (svg) svg.remove();
			const w = node.clientWidth;
			const h = node.clientHeight;
			const groups = groupPeriods(months, period);
			const sums = groups.map((g) => chart.series.map((s) => g.months.reduce((t, i) => t + s.values[i], 0)));
			const totals = sums.map((row) => row.reduce((a, b) => a + b, 0));
			const isShare = mode === "share";
			const shown = sums.map((row, gi) => row.map((v) => (isShare ? (totals[gi] ? (v * 100) / totals[gi] : 0) : v)));

			const scale = isShare ? { max: 100, ticks: [0, 25, 50, 75, 100] } : niceScale(Math.max(...totals, 1), 4);
			const m = { top: 8, right: 4, bottom: 22, left: 34 };
			const plotW = w - m.left - m.right;
			const plotH = h - m.top - m.bottom;
			const band = plotW / groups.length;
			const barW = Math.max(3, Math.min(24, band - (band > 12 ? 4 : 2)));
			const y = (v) => m.top + plotH * (1 - v / scale.max);

			svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": `${chart.title} par ${period === "year" ? "année" : period === "quarter" ? "trimestre" : "mois"}` });
			node.insertBefore(svg, node.firstChild);

			const grid = cssVar(node, "--viz-grid");
			const line = cssVar(document.documentElement, "--line") || "#e7e1d7";
			const muted = cssVar(document.documentElement, "--muted") || "#6b7280";
			const highlight = el("rect", { y: m.top, width: band, height: plotH, fill: "#f7f4ef", rx: 4, visibility: "hidden" }, svg);

			scale.ticks.forEach((t) => {
				el("line", { x1: m.left, x2: w - m.right, y1: y(t), y2: y(t), stroke: grid, "stroke-width": 1 }, svg);
				const text = el("text", { x: m.left - 6, y: y(t), "text-anchor": "end", "dominant-baseline": "middle", fill: muted, "font-size": 10 }, svg);
				text.textContent = isShare ? `${t} %` : intFmt.format(t);
			});

			// Axe des périodes : années sous l'axe (mois, trimestres) ou libellé direct (années).
			groups.forEach((g, gi) => {
				const x0 = m.left + band * gi;
				const newYear = gi > 0 && groups[gi - 1].year !== g.year;
				if (period !== "year") {
					if (newYear) el("line", { x1: x0, x2: x0, y1: m.top, y2: h - m.bottom + 4, stroke: line, "stroke-width": 1 }, svg);
					if (gi === 0 || newYear) {
						const text = el("text", { x: x0 + 3, y: h - 6, fill: muted, "font-size": 10, "font-weight": 600 }, svg);
						text.textContent = g.year;
					}
				} else {
					const text = el("text", { x: x0 + band / 2, y: h - 6, "text-anchor": "middle", fill: muted, "font-size": 11, "font-weight": 600 }, svg);
					text.textContent = g.label;
				}
			});

			// Segments empilés, séparés par 2 px de fond ; arrondi sur le segment du haut.
			groups.forEach((g, gi) => {
				const x = m.left + band * gi + (band - barW) / 2;
				let base = 0;
				const visible = shown[gi].map((v, si) => [v, si]).filter(([v]) => v > 0);
				visible.forEach(([v, si], k) => {
					const top = y(base + v);
					const bottom = y(base);
					const isTop = k === visible.length - 1;
					const gap = isTop ? 0 : 2;
					el("path", {
						d: isTop
							? barPath(x, top, barW, bottom - top)
							: `M${x},${top + gap}h${barW}v${Math.max(0, bottom - top - gap)}h${-barW}Z`,
						fill: chart.series[si].color,
						"fill-opacity": g.partial ? 0.55 : 1,
					}, svg);
					base += v;
				});
			});

			groups.forEach((g, gi) => {
				const x0 = m.left + band * gi;
				const hit = el("rect", { x: x0, y: m.top, width: band, height: plotH, fill: "transparent" }, svg);
				hit.addEventListener("pointerenter", () => {
					highlight.setAttribute("x", x0);
					highlight.setAttribute("visibility", "visible");
					const rows = chart.series
						.map((s, si) => [s, sums[gi][si]])
						.reverse()
						.map(([s, v]) => {
							const pct = totals[gi] ? Math.round((v * 100) / totals[gi]) : 0;
							return `<div class="tt-row"><i class="legend-swatch" style="background:${s.color}"></i>${s.label}<b>${intFmt.format(v)} <small>· ${pct} %</small></b></div>`;
						});
					tooltip.show(
						`<div class="tt-title">${g.label}${g.partial ? " (en cours)" : ""} · ${intFmt.format(totals[gi])}</div>${rows.join("")}`,
						x0 + band / 2,
						m.top + plotH * 0.35
					);
				});
				hit.addEventListener("pointerleave", () => {
					highlight.setAttribute("visibility", "hidden");
					tooltip.hide();
				});
			});
		}

		onResize(node, draw);
		return (next) => {
			if (next.period) period = next.period;
			if (next.mode) mode = next.mode;
			draw();
		};
	}

	// Baguettes, verres, passe-partout côte à côte par période. En mode « part » :
	// verres et passe-partout en % des encadrements (la baguette ferait toujours 100 %).
	function drawGrouped(node, legend, chart, months) {
		const tooltip = makeTooltip(node);
		let period = "quarter";
		let mode = "count";
		let svg;

		function draw() {
			if (!node.clientWidth) return; // vue masquée : dessinée quand elle s'affiche
			if (svg) svg.remove();
			const w = node.clientWidth;
			const h = node.clientHeight;
			const isShare = mode === "share";
			const series = isShare ? chart.series.filter((s) => s.key !== "wand") : chart.series;
			legend.innerHTML = series
				.map((s) => `<span><i class="legend-swatch" style="background:${s.color}"></i>${s.label}${isShare ? " (% des encadrements)" : ""}</span>`)
				.join("");

			const groups = groupPeriods(months, period);
			const sum = (values, g) => g.months.reduce((t, i) => t + values[i], 0);
			const bases = groups.map((g) => sum(chart.base, g));
			const raw = groups.map((g) => series.map((s) => sum(s.values, g)));
			const shown = raw.map((row, gi) => row.map((v) => (isShare ? (bases[gi] ? (v * 100) / bases[gi] : 0) : v)));

			const scale = isShare ? { max: 100, ticks: [0, 25, 50, 75, 100] } : niceScale(Math.max(...shown.flat(), 1), 4);
			const m = { top: 8, right: 4, bottom: 22, left: 34 };
			const plotW = w - m.left - m.right;
			const plotH = h - m.top - m.bottom;
			const band = plotW / groups.length;
			const barW = Math.max(2, Math.min(14, (band - 4) / series.length - 2));
			const y = (v) => m.top + plotH * (1 - v / scale.max);

			svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": chart.title });
			node.insertBefore(svg, node.firstChild);

			const grid = cssVar(node, "--viz-grid");
			const line = cssVar(document.documentElement, "--line") || "#e7e1d7";
			const muted = cssVar(document.documentElement, "--muted") || "#6b7280";
			const highlight = el("rect", { y: m.top, width: band, height: plotH, fill: "#f7f4ef", rx: 4, visibility: "hidden" }, svg);

			scale.ticks.forEach((t) => {
				el("line", { x1: m.left, x2: w - m.right, y1: y(t), y2: y(t), stroke: grid, "stroke-width": 1 }, svg);
				const text = el("text", { x: m.left - 6, y: y(t), "text-anchor": "end", "dominant-baseline": "middle", fill: muted, "font-size": 10 }, svg);
				text.textContent = isShare ? `${t} %` : intFmt.format(t);
			});

			groups.forEach((g, gi) => {
				const x0 = m.left + band * gi;
				const newYear = gi > 0 && groups[gi - 1].year !== g.year;
				if (period !== "year") {
					if (newYear) el("line", { x1: x0, x2: x0, y1: m.top, y2: h - m.bottom + 4, stroke: line, "stroke-width": 1 }, svg);
					if (gi === 0 || newYear) {
						const text = el("text", { x: x0 + 3, y: h - 6, fill: muted, "font-size": 10, "font-weight": 600 }, svg);
						text.textContent = g.year;
					}
				} else {
					const text = el("text", { x: x0 + band / 2, y: h - 6, "text-anchor": "middle", fill: muted, "font-size": 11, "font-weight": 600 }, svg);
					text.textContent = g.label;
				}
				const width = series.length * barW + (series.length - 1) * 2;
				series.forEach((s, si) => {
					const v = shown[gi][si];
					const x = x0 + (band - width) / 2 + si * (barW + 2);
					el("path", { d: barPath(x, y(v), barW, y(0) - y(v)), fill: s.color, "fill-opacity": g.partial ? 0.55 : 1 }, svg);
				});
			});

			groups.forEach((g, gi) => {
				const x0 = m.left + band * gi;
				const hit = el("rect", { x: x0, y: m.top, width: band, height: plotH, fill: "transparent" }, svg);
				hit.addEventListener("pointerenter", () => {
					highlight.setAttribute("x", x0);
					highlight.setAttribute("visibility", "visible");
					const rows = chart.series.map((s) => {
						const v = sum(s.values, g);
						const pct = bases[gi] ? Math.round((v * 100) / bases[gi]) : 0;
						const extra = s.key === "wand" ? "" : ` <small>· ${pct} % des encadrements</small>`;
						return `<div class="tt-row"><i class="legend-swatch" style="background:${s.color}"></i>${s.label}<b>${intFmt.format(v)}${extra}</b></div>`;
					});
					tooltip.show(`<div class="tt-title">${g.label}${g.partial ? " (en cours)" : ""}</div>${rows.join("")}`, x0 + band / 2, m.top + plotH * 0.35);
				});
				hit.addEventListener("pointerleave", () => {
					highlight.setAttribute("visibility", "hidden");
					tooltip.hide();
				});
			});
		}

		onResize(node, draw);
		return (next) => {
			if (next.period) period = next.period;
			if (next.mode) mode = next.mode;
			draw();
		};
	}

	function initTrends() {
		const data = readJson("trends-data");
		if (!data || !data.months.length) return;
		const updaters = data.charts
			.map((chart) => {
				const node = document.querySelector(`[data-trend-chart="${chart.id}"]`);
				const legend = document.querySelector(`[data-trend-legend="${chart.id}"]`);
				return node && legend ? drawTrend(node, legend, chart, data.months) : null;
			})
			.filter(Boolean);

		// Baguettes, verres, passe-partout : une vue d'ensemble + le détail de chacun.
		const comp = data.components;
		const card = document.querySelector("[data-components]");
		if (comp && card) {
			const views = {};
			const make = (id, drawer, chart) => {
				const view = card.querySelector(`[data-view="${id}"]`);
				const update = drawer(view.querySelector("[data-chart]"), view.querySelector("[data-legend]"), chart, data.months);
				views[id] = { view, update };
				updaters.push(update);
			};
			make("all", drawGrouped, comp);
			comp.details.forEach((detail) => make(detail.id, drawTrend, detail));
			const buttons = card.querySelectorAll("[data-components-view] button");
			buttons.forEach((button) => {
				button.addEventListener("click", () => {
					buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
					Object.keys(views).forEach((id) => (views[id].view.hidden = id !== button.dataset.value));
					views[button.dataset.value].update({});
				});
			});
		}

		[["[data-trend-period]", "period"], ["[data-trend-mode]", "mode"]].forEach(([selector, name]) => {
			const group = document.querySelector(selector);
			if (!group) return;
			const buttons = group.querySelectorAll("button");
			buttons.forEach((button) => {
				button.addEventListener("click", () => {
					buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
					updaters.forEach((update) => update({ [name]: button.dataset.value }));
				});
			});
		});
	}

	// Boutons de mesure : chacun pilote le graphique de sa propre carte.
	function bindToggle(card, setMetric) {
		const buttons = card.querySelectorAll(".chart-toggle button");
		buttons.forEach((button) => {
			button.addEventListener("click", () => {
				const metric = button.dataset.metric;
				buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
				card.querySelectorAll("[data-metric-note]").forEach((note) => {
					note.hidden = note.dataset.metricNote !== metric;
				});
				card.querySelectorAll("[data-metric-table]").forEach((table) => {
					table.hidden = table.dataset.metricTable !== metric;
				});
				setMetric(metric);
			});
		});
	}

	function init() {
		const kpis = readJson("kpi-data") || [];
		kpis.forEach((kpi) => {
			const node = document.querySelector(`[data-spark="${kpi.id}"]`);
			if (node && kpi.spark.length > 1) drawSparkline(node, kpi.spark, kpi.format);
		});

		initTrends();

		const history = readJson("history-data");
		const chart = document.getElementById("years-chart");
		if (history && history.length && chart) {
			const card = chart.closest("[data-chart-card]");
			bindToggle(card, drawYears(chart, history, card.querySelector("[data-years-legend]")));
		}
	}

	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
	else init();
})();
