

function formatCurrency(amount) {
    if (amount === null || amount === undefined) {
        return '';
    }
    /*Get web language*/
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
            detail_url = "{% url 'funding_request_detail' funding_request.id %}"
            $('#fundings-container').append(`
            <div class="col s12 m12 l4">
                <div class="card hoverable funding-card">
                    <div class="card-image">
                        <span class="yellow category">${funding_request.funding_request_status}</span>
                        <img src="${funding_request.principal_image_url ? funding_request.principal_image_url : '{% static "img/articles/img1.avif" %}'}" alt="Description de l'image">
                        <span class="card-title white opacity-08 black-text">${funding_request.beneficiary_name}</span>
                    </div>
                    <div class="card-content card-highlight-title">
                        <p data-fulltext="${funding_request.title}">${funding_request.title}</p>
                        <p>Montant: <b>${formatCurrency(funding_request.amount)}</b></p>
                        <div class="progress">
                            <div class="determinate" style="width: ${funding_request.progress}%"></div>
                        </div>
                        <p>${funding_request.progress}% collecté</p>
                        <p>Temps restant: ${funding_request.days_remaining} jours</p>
                    </div>
                    <div class="card-action card-action-share">
                        <div>
                            <a id="${funding_request.id}-funddetails" href="${funding_request.details_url}">PLUS D'INFOS</a>
                        </div>
                        <div>
                            <!--Social media sharing buttons-->
                            <span class="right social-icone"><a href="#" title="facebook" class="btn-floating btn-small blue"><i class="mdi-facebook">F</i></a></span>
                            <span class="right social-icone"><a href="#" title="X" class="btn-floating btn-small black"><i class="material-icons">F</i></a></span>
                            <span class="right social-icone"><a href="#" title="linkedIn" class="btn-floating btn-small red"><i class="material-icons">mail</i></a></span>           
                        </div>
                    </div>
                </div>
            </div>
        `);
        });
    }
    // Gère la pagination
    $('#pagination').empty();
    if (response.pagination.has_previous) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page - 1}">Precedent
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

        // Utiliser la balise {% url %} pour générer l'URL dynamique
        const apiUrl = "/api/funding-requests/?page=" + page + "&items_per_page=" + itemsPerPage;

        formData = $('#filterForm').serialize()


        $.ajax({
            url: apiUrl, // Appel à l'API avec paramètres de pagination
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function (response) {
                // Masquer le loader
                $('#loader').hide();

                // Efface le contenu existant
                $('#fundings-container').empty();

                GenerateFundingRequestList(response);

            },
            error: function (xhr, status, error) {
                // Masquer le loader en cas d'erreur
                $('#loader').hide();
                $('#fundings-container').empty();
                $('#fundings-container').append(` <div class="col s12 m12 l12"> 
                    <div class="card-panel">
                        <h5 data-fulltext="Aucun" class="center red-text"> Erreur lors du chargement des demandes de financement </h5>
                    </div>
                </div>
                    `);
                console.log("Erreur lors du chargement des éléments : ", error);
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
        event.preventDefault(); // Empêche le rechargement de la page

        // Affiche le loader
        $('#loader').show();

        // Récupère les données du formulaire
        const csrftoken = $('input[name=csrfmiddlewaretoken]').val();
        let formData = $(this).serializeArray();

        // Convertit les dates du format dd-mm-yyyy vers yyyy-mm-dd
        formData = formData.map(field => {
            if (field.name === 'start_date' || field.name === 'end_date') {
                field.value = convertToSQLDate(field.value);
            }
            return field;
        });

        // Transformation en objet URL-encoded
        const encodedData = $.param(formData);

        const page = 1;
        const itemsPerPage = 9;
        const apiUrl = `/api/funding-requests/?page=${page}&items_per_page=${itemsPerPage}`;

        $('#fundings-container').empty();
        console.log("Data", encodedData);

        // Envoie une requête AJAX
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



});