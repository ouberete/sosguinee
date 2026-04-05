
function formatCurrency(amount) {
    if (amount === null || amount === undefined) {
        return '';
    }
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'GNF',
    }).format(amount);
}

function GenerateFundingRequestList(response) {

    $('#pagination').empty();

    // Affiche les éléments
    if (response.funding_requests.length == 0) {
        $('#fundings-container').append(`
            <div class="col s12 m12 l12">
                <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center">Aucune donnée à afficher</h5>
                </div>
            </div>
        `)
        $('#loader').hide()
        return
    } else {
        // Affiche la liste
        response.funding_requests.forEach(function (funding_request) {
            const statusLabel = funding_request.funding_request_status || 'En attente';
            const daysText = (funding_request.days_remaining !== null && funding_request.days_remaining !== undefined)
                ? `${funding_request.days_remaining} jours restants`
                : 'Date non définie';
            const imgSrc = funding_request.principal_image_url
                ? funding_request.principal_image_url
                : '/static/img/articles/img1.avif';

            const closeBtn = funding_request.is_creator && funding_request.funding_request_status !== 'Clos' && funding_request.funding_request_status !== 'Trouvé'
                ? `<button class="btn waves-effect waves-light grey darken-1 close-btn" data-public-id="${funding_request.public_id}" data-close-url="${funding_request.close_url}" onclick="return confirm('Voulez-vous vraiment clôturer cette demande de financement ?')">
                     <i class="material-icons left">check_circle</i> Clôturer
                   </button>`
                : '';

            $('#fundings-container').append(`
            <div class="col s12 m12 l4">
                <div class="card hoverable funding-card">
                    <div class="card-image">
                        <span class="badge">${statusLabel}</span>
                        <img src="${imgSrc}" alt="${funding_request.beneficiary_name}" loading="lazy">
                        <span class="card-title white opacity-08 black-text">${funding_request.beneficiary_name}</span>
                    </div>
                    <div class="card-content card-highlight-title">
                        <p data-fulltext="${funding_request.title}"><strong>${funding_request.title}</strong></p>
                        <p>Montant: <b>${formatCurrency(funding_request.amount)}</b></p>
                        <div class="progress">
                            <div class="determinate" style="width: ${funding_request.progress}%"></div>
                        </div>
                        <p>${funding_request.progress}% collecté</p>
                        <p>${daysText}</p>
                    </div>
                    <div class="card-action card-action-share">
                        <div>
                            <a id="${funding_request.id}-funddetails" href="${funding_request.details_url}" class="blue-text text-darken-2">PLUS D'INFOS</a>
                        </div>
                        <div>
                            <a href="#" title="Twitter" class="social-icon" aria-label="Partager sur Twitter"><i class="fab fa-twitter"></i></a>
                            <a href="#" title="Facebook" class="social-icon" aria-label="Partager sur Facebook"><i class="fab fa-facebook-f"></i></a>
                        </div>
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
                               <i class="material-icons left">chevron_left</i>
                           </button>`);
    }
    $('#pagination').append(`<span>&nbsp;&nbsp;Page ${response.pagination.current_page} sur ${response.pagination.total_pages}</span>`);
    if (response.pagination.has_next) {
        $('#pagination').append(` <button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
                               <i class="material-icons right">chevron_right</i>
                           </button>`);
    }
}

$(document).ready(function () {

    // Fonction pour charger les éléments avec pagination
    function loadFundingRequests(page = 1, itemsPerPage = 9) {
        // Afficher le loader
        $('#loader').show();

        const apiUrl = "/api/funding-requests/?page=" + page + "&items_per_page=" + itemsPerPage;

        formData = $('#filterForm').serialize()


        $.ajax({
            url: apiUrl,
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function (response) {
                $('#loader').hide();
                $('#fundings-container').empty();
                GenerateFundingRequestList(response);
            },
            error: function (xhr, status, error) {
                $('#loader').hide();
                $('#fundings-container').empty();
                $('#fundings-container').append(` <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center red-text"> Erreur lors du chargement des demandes de financement </h5>
                    </div>
                </div>
                    `);
                console.error("Erreur lors du chargement des éléments : ", error);
            }
        });
    }

    // Charger les éléments de la page 1 au démarrage
    loadFundingRequests();

    // Gestion des clics sur les boutons de pagination
    $('#pagination').on('click', '.btn-page', function () {
        const page = $(this).data('page');
        loadFundingRequests(page);
    });


// Intercepte la soumission du formulaire
    $('#filterForm').submit(function (event) {
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
        const apiUrl = `/api/funding-requests/?page=${page}&items_per_page=${itemsPerPage}`;

        $('#fundings-container').empty();

        $.ajax({
            url: apiUrl,
            type: 'GET',
            data: encodedData,
            success: function (response) {
                $('#loader').hide();
                GenerateFundingRequestList(response);
            },
            error: function (error) {
                $('#loader').hide();
                $('#fundings-container').empty();
                $('#fundings-container').append(`
                <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 class="center red-text">Erreur lors du chargement des demandes de financement</h5>
                    </div>
                </div>
            `);
            }
        });
    });

// Fonction de conversion
    function convertToSQLDate(dateStr) {
        if (!dateStr) return '';
        const [day, month, year] = dateStr.split('-');
        if (!day || !month || !year) return '';
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }

    // Gestion de la clôture des demandes de financement
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
                M.toast({html: 'Demande clôturée avec succès.', classes: 'green'});
                // Recharger la liste pour mettre à jour le statut
                loadFundingRequests(1);
            },
            error: function(xhr) {
                let errorMsg = 'Erreur lors de la clôture.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Vous n\'êtes pas autorisé à clôturer cette demande.';
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