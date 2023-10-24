$(function() {
    $("#id_last_name").autocomplete({
        source: "/get_clients/",
        minLength: 2,
        select: function(event, ui) {
            $('#id_first_name').val(ui.item.first_name);
            $('#id_last_name').val(ui.item.last_name);
            $('#id_phone_number').val(ui.item.phone_number);
            $('#id_address').val(ui.item.address);
            $('#id_mail').val(ui.item.mail);
            $('#id_customer').val(ui.item.id);
            return false;
        }
    });
});
