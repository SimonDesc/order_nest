$(document).ready(function () {
	const idOrder = $("#orderPk").val();

	// Calling the functions by default
	getBalance();

	$("#sms").on("click", function () {
		sendSms();
	});


	function sendSms() {
		return fetch(`/send_sms/`)
			.then(response => {
				if (!response.ok) {
					throw new Error('Erreur réseau ou réponse avec statut échoué.');
				}
				// console.log(response.json())
			})
			.catch(error => {
				console.error("Il y a eu un problème avec l'opération fetch:", error);
			});
	}


	// Count the lenght of the sms
	(function ($) {
		$.fn.smsArea = function (options) {

			var e = this,
				cutStrLength = 0,

				s = $.extend({

					cut: true,
					maxSmsNum: 2, // Ajusté pour 2 SMS max
					interval: 400,

					counters: {
						message: $('#smsCount'),
						character: $('#smsLength')
					},

					lengths: {
						ascii: [160, 306, 459],
						unicode: [70, 134, 201]
					}
				}, options);

			function updateMaxLength() {
				var maxLength = s.isUnicode ? s.lengths.unicode[1] : s.lengths.ascii[1];
				e.attr('maxlength', maxLength);
			}

			e.keyup(function () {

				clearTimeout(this.timeout);
				this.timeout = setTimeout(function () {

					var smsType,
						smsLength = 0,
						smsCount = -1,
						charsLeft = 0,
						text = e.val(),
						isUnicode = false;

					for (var charPos = 0; charPos < text.length; charPos++) {
						switch (text[charPos]) {
							case "\n":
							case "[":
							case "]":
							case "\\":
							case "^":
							case "{":
							case "}":
							case "|":
							case "€":
								smsLength += 2;
								break;

							default:
								smsLength += 1;
						}

						if (text.charCodeAt(charPos) > 127 && text[charPos] != "€") isUnicode = true;
					}
					// Deactivate the unicode for now (not necessary)
					// s.isUnicode = isUnicode;

					// if (isUnicode) {
					// 	smsType = s.lengths.unicode;

					// } else {
					smsType = s.lengths.ascii;
					// }

					for (var sCount = 0; sCount < s.maxSmsNum; sCount++) {

						cutStrLength = smsType[sCount];
						if (smsLength <= smsType[sCount]) {

							smsCount = sCount + 1;
							charsLeft = smsType[sCount] - smsLength;
							break;
						}
					}

					if (s.cut) e.val(text.substring(0, cutStrLength));
					smsCount == -1 && (smsCount = s.maxSmsNum, charsLeft = 0);

					s.counters.message.html(smsCount);
					s.counters.character.html(charsLeft);

					updateMaxLength();

				}, s.interval);
			}).keyup();
		}
	})(jQuery);


	// Param for sms type
	$('.exclusive-checkbox').change(function () {
		if ($(this).is(':checked')) {
			// Désélectionnez toutes les cases à cocher
			$('.exclusive-checkbox').prop('checked', false);
			// Cochez la case sélectionnée
			$(this).prop('checked', true);

			orderId = $('#id-commande').text();
			orderName = $('#name-commande').text().trim();

			if ($(this).attr('id') === 'prise-en-charge-checkbox-list') {
				$("#sms-input").val(`Bonjour ${orderName}, commande numéro ${orderId} bien recue !
Galerie Libre Cours vous remercie.
Suivi et info: 05 62 18 91 84
`);
			}
			else if ($(this).attr('id') === 'commande-terminee-checkbox-list') {
				$("#sms-input").val(`Bonjour,

Votre commande est disponible à la galerie Libre Cours à Revel.
Bien cordialement
Encadrement - Restauration de tableaux
Infos: 06.50.80.77.23
`);
			}
			else if ($(this).attr('id') === 'autre-checkbox-list') {
				$("#sms-input").val(`

Galerie Libre Cours vous remercie.
Suivi et info: 05 62 18 91 84
`);
			}
			$('#sms-input').smsArea();

		}
	});


	// Get the credits
	function getBalance() {
		$.ajax({
			url: '/get_credit_sms/',
			type: "GET",
			dataType: "json",
			success: function (response) {
				if (response.success === true) {
					let creditSms = response.data.credits.creditSms;
					$("#creditSms").append(creditSms)
				} else {
					$("#creditSms").append("Erreur")
				}
			},
			error: function (xhr, status, error) {
				// Traitement en cas d'erreur lors de la requête
				$("#creditSms").append("Erreur")
				console.log("Erreur lors de la requête: ", error);
			}
		});
	}

	// Get history of sms
	// function getHistory() {
	// 	let phone_number = $('#phone-input').val();
	// 	// Aadd the phone number to the URL
	// 	let urlWithParam = '/get_history_sms/?phone_number=' + encodeURIComponent('+33669171357');

	// 	$.ajax({
	// 		url: urlWithParam,
	// 		type: "GET",
	// 		dataType: "json",
	// 		success: function (response) {
	// 			if (response.success === true) {
	// 				console.log("history true:", response);
	// 			} else {
	// 				console.log("history false:", response);
	// 			}
	// 		},
	// 		error: function (xhr, status, error) {
	// 			console.log("Erreur lors de la requête: ", error);
	// 		}
	// 	});
	// }



})

