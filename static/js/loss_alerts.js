function GenerateLossAlertList(response) {
    $('#pagination').empty();

    // Affiche les éléments
    if (response.loss_alerts.length == 0) {
        $('#alerts-container').append(`
            <div class="col s12 m12 l12">
                <div class="card-panel">
                    <h5 data-fulltext="Aucun" class="center">Aucune alerte à afficher</h5>
                </div>
            </div>
        `);
        $('#loader').hide();
        return;
    } else {
        // Affiche la liste
        response.loss_alerts.forEach(function(loss_alert) {
            $('#alerts-container').append(`
                <div class="col s12 m12 l4">
                    <div class="card card-alert card-main">
                        <div class="card-image">
                            <span class="yellow category">${loss_alert.status_alert_name}</span>
                            <img src="${loss_alert.principal_image_url ? loss_alert.principal_image_url : '{% static "img/articles/img1.avif" %}'}" alt="Image principale">
                            <span class="card-title blue opacity-08 white-text">${loss_alert.name}</span>
                        </div>
                        <div class="card-content">
                            <p><b>Type d'alerte : </b>${loss_alert.type_alert_name}</p>
                            <p><b>Date : </b>${loss_alert.date_alert}</p>
                            <p><b>Heure : </b>${loss_alert.hour_alert}</p>
                        </div>
                        <div class="card-action">
                            <a href="${loss_alert.details_url}" id="${loss_alert.id}-dalerte" class="btn red">Voir Détails</a>
                            <a href="#" id="${loss_alert.id}-alertcontact" class="btn blue right">Contacter</a>
                        </div>
                    </div>
                </div>
            `);
        });
    }

    // Gère la pagination
    $('#pagination').empty();
    if (response.pagination.has_previous) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page - 1}">Précédent
                                 <i class="material-icons left">chevron_left</i></button>`);
    }
    $('#pagination').append(`<span>&nbsp;&nbsp;Page ${response.pagination.current_page} sur ${response.pagination.total_pages}</span>`);
    if (response.pagination.has_next) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
                                 <i class="material-icons right">chevron_right</i></button>`);
    }
}

$(document).ready(function() {
    // Fonction pour charger les éléments avec pagination
    function loadLossAlerts(page = 1, itemsPerPage = 9) {
        // Afficher le loader
        $('#loader').show();

        const apiUrl = "/api/loss-alerts/?page=" + page + "&items_per_page=" + itemsPerPage;
        const formData = $('#filterForm').serialize();

        $.ajax({
            url: apiUrl, // Appel à l'API avec paramètres de pagination
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function(response) {
                // Masquer le loader
                $('#loader').hide();

                // Efface le contenu existant
                $('#alerts-container').empty();

                GenerateLossAlertList(response);
            },
            error: function(xhr, status, error) {
                // Masquer le loader en cas d'erreur
                $('#loader').hide();
                $('#alerts-container').empty();
                $('#alerts-container').append(` <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center red-text"> Erreur lors du chargement des alertes </h5>
                    </div>
                </div>
                    `);
                console.log("Erreur lors du chargement des alertes : ", error);
            }
        });
    }

    // Charger les éléments de la page 1 au démarrage
    loadLossAlerts();

    // Gestion des clics sur les boutons de pagination
    $('#pagination').on('click', '.btn-page', function() {
        const page = $(this).data('page');
        loadLossAlerts(page);
    });

    // Interception de la soumission du formulaire
    $('#filterForm').submit(function(event) {
        event.preventDefault();
        $('#loader').show();
        
        const formData = $(this).serialize();
        const page = 1;
        const itemsPerPage = 9;
        const apiUrl = "/api/loss-alerts/?page=" + page + "&items_per_page=" + itemsPerPage;
        
        $('#alerts-container').empty();

        $.ajax({
            url: apiUrl,
            type: 'GET',
            data: formData,
            dataType: 'json',
            success: function(response) {
                $('#loader').hide();
                GenerateLossAlertList(response);
            },
            error: function(error) {
                $('#loader').hide();
                $('#alerts-container').empty();
                $('#alerts-container').append(` <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center red-text"> Erreur lors du chargement des alertes </h5>
                    </div>
                </div>
                    `);
                console.log('Erreur:', error);
            }
        });
    });
});
