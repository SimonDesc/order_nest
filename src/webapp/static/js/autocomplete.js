$(function() {
    $("#id_last_name").autocomplete({
        source: "/get_clients/",
        minLength: 2,
        open: function() {

            // Styles et classes pour le conteneur du menu déroulant
            $(".ui-autocomplete").addClass(
                "absolute top-full left-0 z-[1000] min-w-[200px] max-w-[300px] " +
                "py-2 border border-gray-300 rounded-lg shadow-lg bg-white"
            );

            // Fait en sorte que chaque élément de menu occupe toute la largeur disponible
            $(".ui-menu-item").addClass("w-full");

            // Styles pour le contenu de chaque élément de menu
            $(".ui-menu-item-wrapper").addClass(
                "w-full text-lg text-gray-900 py-2 px-4 " +
                "hover:bg-gray-200 hover:text-black cursor-pointer"
            );

            // Fixe la largeur du conteneur du menu déroulant à 220px ou à une autre valeur que vous préférez
            $(".ui-autocomplete").css("width", "220px");

            // Supprime les éléments inaccessibles qui ne sont pas nécessaires
            $(".ui-helper-hidden-accessible").remove();

        },
        select: function(event, ui) {
            $('#id_first_name').val(ui.item.first_name);
            $('#id_last_name').val(ui.item.last_name);
            $('#id_phone_number').val(ui.item.phone_number);
            $('#id_address').val(ui.item.address);
            $('#id_mail').val(ui.item.mail);
            $('#id_customer').val(ui.item.id);
            return false;
        },
        response: function(event, ui) {
            if (ui.content.length === 0) {
                ui.content.push({ label: "Aucun résultat trouvé", value: "" });
            }
        }
    });
});