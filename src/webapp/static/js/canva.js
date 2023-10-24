$(document).ready(function() {
    paper.setup($('#drawZone')[0]);
    let tool = new paper.Tool();
    let path;

    tool.onMouseDown = function(event) {
        path = new paper.Path();
        path.strokeColor = 'black';
        path.add(event.point);
    }

    tool.onMouseDrag = function(event) {
        path.add(event.point);
    }

    // Ecouteur bouton Effacer
    $("#bt_eraseDrawing").click(eraseDrawing);

    // Ecouteur bouton Sauvegarder
    $("#bt_saveDrawing").click(function() {
    const canvas = $('#drawZone')[0];
    const dataURL = canvas.toDataURL();
    const csrfToken = $("[name=csrfmiddlewaretoken]").val();
    const idOrder = $("#orderPk").val();
    const canvasName = $("#canvasList");

    fetch("/save_canvas/", {
            method: "POST",
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                img: dataURL,
                order_id: idOrder
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur réseau ou réponse avec statut échoué.');
            }
            return response.text();
        })
        .then(file => {
            eraseDrawing();
            canvasName.append('<li>' + file + '<li>');
        })
        .catch(error => {
            console.error("Il y a eu un problème avec l'opération fetch:", error);
        });
    });

    $(".delete_canvas").click(function() {
        const csrfToken = $("[name=csrfmiddlewaretoken]").val();
        const canvasId = $(this).data("pk");
        console.log("test");
        console.log(canvasId)
        fetch(`/delete_canvas/${canvasId}`, {
            method : 'DELETE',
            headers : {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                canvas_id : canvasId
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
            console.log(data);
            location.reload();
        })
        .catch(error => {
            console.error("Erreur : ", error);
        })
    });

});



function eraseDrawing() {
    var canvas = $('#drawZone')[0];
    var context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    paper.project.clear();
}

