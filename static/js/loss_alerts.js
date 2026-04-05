function convertToSQLDate(dateStr) {
    if (!dateStr) return '';
    const [day, month, year] = dateStr.split('-');
    if (!day || !month || !year) return '';
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

function GenerateLossAlertList(response) {
    $('#pagination').empty();

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
        response.loss_alerts.forEach(function(loss_alert) {
            const statusLabel = loss_alert.status_alert_name || 'En attente';
            const imgSrc = loss_alert.principal_image_url
                ? loss_alert.principal_image_url
                : '/static/img/articles/img1.avif';
            const phoneLink = loss_alert.phone
                ? `<a href="tel:${loss_alert.phone}" class="btn blue right" aria-label="Appeler pour ${loss_alert.name}"><i class="material-icons left">call</i>Contacter</a>`
                : '';

            const closeBtn = loss_alert.is_creator && loss_alert.status_alert_name !== 'Clos' && loss_alert.status_alert_name !== 'Trouvé' && loss_alert.status_alert_name !== 'Résolu' && loss_alert.status_alert_name !== 'Retrouvé'
                ? `<button class="btn waves-effect waves-light grey darken-1 close-btn" data-public-id="${loss_alert.public_id}" data-close-url="${loss_alert.close_url}" onclick="return confirm('Voulez-vous vraiment clôturer cette alerte ?')">
                     <i class="material-icons left">check_circle</i> Clôturer
                   </button>`
                : '';

            $('#alerts-container').append(`
                <div class="col s12 m12 l4">
                    <div class="card alert-card hoverable">
                        <div class="card-image">
                            <span class="badge">${statusLabel}</span>
                            <img src="${imgSrc}" alt="${loss_alert.name}" loading="lazy">
                            <span class="card-title blue opacity-08 white-text">${loss_alert.name}</span>
                        </div>
                        <div class="card-content">
                            <p><b>Type d'alerte : </b>${loss_alert.type_alert_name}</p>
                            <p><b>Date : </b>${loss_alert.date_alert || ''}</p>
                            <p><b>Heure : </b>${loss_alert.hour_alert || ''}</p>
                        </div>
                        <div class="card-action">
                            <a href="${loss_alert.details_url}" id="${loss_alert.id}-dalerte" class="btn red" aria-label="Voir les détails de ${loss_alert.name}">Voir Détails</a>
                            ${phoneLink}
                            ${closeBtn ? `<div style="margin-top: 10px;">${closeBtn}</div>` : ''}
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
    function loadLossAlerts(page = 1, itemsPerPage = 9) {
        $('#loader').show();

        const apiUrl = "/api/loss-alerts/?page=" + page + "&items_per_page=" + itemsPerPage;
        const formData = $('#filterForm').serialize();

        $.ajax({
            url: apiUrl,
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function(response) {
                $('#loader').hide();
                $('#alerts-container').empty();
                GenerateLossAlertList(response);
            },
            error: function(xhr, status, error) {
                $('#loader').hide();
                $('#alerts-container').empty();
                $('#alerts-container').append(` <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center red-text"> Erreur lors du chargement des alertes </h5>
                    </div>
                </div>
                    `);
                console.error("Erreur lors du chargement des alertes : ", error);
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

        const csrftoken = $('input[name=csrfmiddlewaretoken]').val();
        let formData = $(this).serializeArray();

        // Convertit les dates du format dd-mm-yyyy vers yyyy-mm-dd
        formData = formData.map(field => {
            if (field.name === 'start_date' || field.name === 'end_date') {
                field.value = convertToSQLDate(field.value);
            }
            return field;
        });

        const encodedData = $.param(formData);

        const page = 1;
        const itemsPerPage = 9;
        const apiUrl = "/api/loss-alerts/?page=" + page + "&items_per_page=" + itemsPerPage;

        $('#alerts-container').empty();

        $.ajax({
            url: apiUrl,
            type: 'GET',
            data: encodedData,
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
            }
        });
    });

    // Gestion de la clôture des alertes de perte
    $(document).on('click', '.close-btn', function(e) {
        e.preventDefault();
        const btn = $(this);
        const closeUrl = btn.data('close-url');
        const publicId = btn.data('public-id');

        $.ajax({
            url: closeUrl,
            type: 'POST',
            headers: {
                'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken')
            },
            success: function(response) {
                M.toast({html: 'Alerte clôturée avec succès.', classes: 'green'});
                // Recharger la liste pour mettre à jour le statut
                loadLossAlerts(1);
            },
            error: function(xhr) {
                let errorMsg = 'Erreur lors de la clôture.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Vous n\'êtes pas autorisé à clôturer cette alerte.';
                }
                M.toast({html: errorMsg, classes: 'red'});
            }
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
