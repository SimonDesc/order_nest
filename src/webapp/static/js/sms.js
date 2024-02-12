$(document).ready(function () {
	const idOrder = $("#orderPk").val();

	function sendSms(idOrder) {

		return fetch(`/send_sms/${idOrder}`)
			.then(response => {
				if (!response.ok) {
					throw new Error('Erreur réseau ou réponse avec statut échoué.');
				}
				console.log(response.json())
				// return response.text();
			})
			.catch(error => {
				console.error("Il y a eu un problème avec l'opération fetch:", error);
			});
	}


	$("#sms").on("click", function () {
		sendSms(idOrder);
	});


	(function($) {
		$.fn.smsArea = function(options) {
	
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
				// Définir la limite à 2 SMS max. Si c'est ASCII, utilisez 306 caractères (pour 2 SMS), sinon 134 pour Unicode.
				var maxLength = s.isUnicode ? s.lengths.unicode[1] : s.lengths.ascii[1];
				e.attr('maxlength', maxLength);
			}
	
			e.keyup(function() {
	
				clearTimeout(this.timeout);
				this.timeout = setTimeout(function() {
	
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
	
					// s.isUnicode = isUnicode; // Stockez si le texte est Unicode pour une utilisation dans updateMaxLength
	
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
	
					updateMaxLength(); // Mettez à jour l'attribut maxlength après chaque frappe de touche
	
				}, s.interval);
			}).keyup();
		}
	})(jQuery);
	
	
	
	$('.exclusive-checkbox').change(function() {
        if ($(this).is(':checked')) {
            // Désélectionnez toutes les cases à cocher
            $('.exclusive-checkbox').prop('checked', false);
            // Cochez la case sélectionnée
            $(this).prop('checked', true);
			
			orderId = $('#id-commande').text();
			orderName = $('#name-commande').text().trim();
			
			if ($(this).attr('id') === 'prise-en-charge-checkbox-list') {
				$("#sms-input").val(`Bonjour ${orderName}, commande n°${orderId} bien reçue !
Galerie Libre Cours vous remercie.
Suivi et info: 05 62 18 91 84`);
			}
			else if ($(this).attr('id') === 'commande-terminee-checkbox-list') {
				$("#sms-input").val(`Votre commande n°${orderId} est prête !
Horaire d'ouverture : du Mardi au Samedi de 09h30 à 12h30 et de 15h à 19h.
05 62 18 91 84`);
			}
			else if ($(this).attr('id') === 'autre-checkbox-list') {
				$("#sms-input").val(`

Galerie Libre Cours vous remercie.
Suivi et info: 05 62 18 91 84`);
			}
			$('#sms-input').smsArea();

        }
    });

	

})

