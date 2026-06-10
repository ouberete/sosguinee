<<<<<<< HEAD


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
=======
function formatCurrency(amount) {
    if (amount === null || amount === undefined || amount === '') {
        return '';
    }
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'GNF',
        maximumFractionDigits: 0,
    }).format(amount);
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function truncateText(value, maxLength = 160) {
    if (!value) {
        return '';
    }
    return value.length > maxLength ? `${value.slice(0, maxLength - 1).trim()}...` : value;
}

function getItemsPerPage() {
    const width = window.innerWidth;
    if (width >= 1400) return 12;
    if (width >= 993) return 9;
    return 6;
}

function showSkeletonLoader(containerId, count) {
    const container = $(containerId);
    container.empty();
    for (let i = 0; i < count; i++) {
        container.append(`
            <div class="col s12 m6 l4">
                <div class="skeleton-card">
                    <div class="skeleton-img"></div>
                    <div class="skeleton-line medium"></div>
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-btn"></div>
                </div>
            </div>
        `);
    }
}

function buildShareUrl(platform, url, title) {
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(title);
    switch (platform) {
        case 'facebook':
            return `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
        case 'twitter':
            return `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`;
        case 'whatsapp':
            return `https://wa.me/?text=${encodedTitle}%20${encodedUrl}`;
        default:
            return '#';
    }
}

function normalizeStatus(value) {
    return (value || '')
        .toString()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
}

function isClosedStatus(statusLabel) {
    const normalized = normalizeStatus(statusLabel);
    return /clos|termine|cloture|trouve|resolu|retrouve/.test(normalized);
}

function getStatusClass(statusLabel, daysRemaining, progress) {
    if (isClosedStatus(statusLabel)) {
        return 'status-closed';
    }
    if ((daysRemaining !== null && daysRemaining !== undefined && daysRemaining <= 7) || progress >= 85) {
        return 'status-urgent';
    }
    return 'status-open';
}

function getProgressClass(progress) {
    if (progress >= 100) return 'high';
    if (progress >= 50) return 'mid';
    return 'low';
}

function renderFundingCard(fundingRequest, index) {
    const statusLabel = fundingRequest.funding_request_status || 'En attente';
    const typeLabel = fundingRequest.funding_request_type_name || 'Financement';
    const daysText = (fundingRequest.days_remaining !== null && fundingRequest.days_remaining !== undefined)
        ? `${fundingRequest.days_remaining} jours restants`
        : 'Sans echeance';
    const imgSrc = fundingRequest.principal_image_url || '/static/img/articles/img1.avif';
    const title = escapeHtml(fundingRequest.title || 'Demande de financement');
    const beneficiaryName = escapeHtml(fundingRequest.beneficiary_name || 'Beneficiaire');
    const description = escapeHtml(truncateText(fundingRequest.description_needs || 'Aucune description disponible.', 160));
    const collectedAmount = formatCurrency(fundingRequest.amount_received || 0);
    const targetAmount = formatCurrency(fundingRequest.amount || 0);
    const remainingAmount = formatCurrency(fundingRequest.remaining_amount || 0);
    const fullUrl = `${window.location.origin}${fundingRequest.details_url}`;
    const paymentUrl = fundingRequest.payment_url || `/funding/${fundingRequest.public_id}/djomy/`;
    const canFund = fundingRequest.can_fund === true || fundingRequest.funding_request_status === 'En cours';
    const shareTitle = `Aide ${fundingRequest.beneficiary_name} - ${fundingRequest.title} - SOS Guinee`;
    const animDelay = `animation-delay: ${index * 0.07}s`;
    const statusClass = getStatusClass(statusLabel, fundingRequest.days_remaining, fundingRequest.progress);
    const progressClass = getProgressClass(fundingRequest.progress);

    const closeBtn = fundingRequest.is_creator && !isClosedStatus(statusLabel)
        ? `<button class="btn waves-effect waves-light grey darken-1 close-btn" data-public-id="${fundingRequest.public_id}" data-close-url="${fundingRequest.close_url}" onclick="return confirm('Voulez-vous vraiment cloturer cette demande de financement ?')">
                <i class="material-icons left">check_circle</i> Cloturer
           </button>`
        : '';

    return `
        <div class="col s12 m6 l4 card-animate" style="${animDelay}">
            <article class="ws-card ws-funding-card" role="article" aria-labelledby="fund-title-${fundingRequest.id}">
                <a class="ws-card-image" href="${fundingRequest.details_url}" aria-label="Voir ${title}">
                    <img src="${imgSrc}" alt="${beneficiaryName}" loading="lazy">
                </a>

                <div class="ws-card-body">
                    <div class="ws-card-status">
                        <span class="ws-card-status-label ${statusClass}">
                            <i class="material-icons">bolt</i>
                            ${escapeHtml(statusLabel)}
                        </span>
                        <span class="ws-card-chip">${escapeHtml(typeLabel)}</span>
                    </div>

                    <h3 id="fund-title-${fundingRequest.id}" class="ws-card-title">
                        <a href="${fundingRequest.details_url}">${title}</a>
                    </h3>

                    <p class="ws-card-beneficiary">
                        <i class="material-icons">person</i>
                        <span>${beneficiaryName}</span>
                    </p>

                    <div class="ws-card-progress">
                        <div class="ws-card-progress-track" role="progressbar" aria-valuenow="${fundingRequest.progress}" aria-valuemin="0" aria-valuemax="100">
                            <div class="ws-card-progress-fill ${progressClass}" style="width: ${fundingRequest.progress}%"></div>
                        </div>
                        <div class="ws-card-progress-meta">
                            <span>${fundingRequest.progress}% collecte</span>
                            <span>${daysText}</span>
                        </div>
                    </div>

                    <p class="ws-card-desc">${description}</p>

                    <div class="ws-card-stats">
                        <div class="ws-card-stat">
                            <div class="ws-card-stat-value">${targetAmount}</div>
                            <div class="ws-card-stat-label">Objectif</div>
                        </div>
                        <div class="ws-card-stat">
                            <div class="ws-card-stat-value">${collectedAmount}</div>
                            <div class="ws-card-stat-label">Collecte</div>
                        </div>
                        <div class="ws-card-stat">
                            <div class="ws-card-stat-value">${remainingAmount}</div>
                            <div class="ws-card-stat-label">Reste</div>
                        </div>
                    </div>

                    <div class="ws-card-action">
                        <a id="${fundingRequest.id}-funddetails" href="${fundingRequest.details_url}" class="btn waves-effect waves-light orange darken-2" aria-label="Voir détails ${title}">
                            Voir détails
                        </a>
                        ${canFund ? `<a href="${paymentUrl}" class="btn-flat ws-card-secondary-action">Financer</a>` : ''}
                    </div>

                    <div class="ws-card-socials">
                        <a href="${buildShareUrl('facebook', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon fb" aria-label="Partager sur Facebook"><i class="fab fa-facebook-f"></i></a>
                        <a href="${buildShareUrl('twitter', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon tw" aria-label="Partager sur Twitter"><i class="fab fa-twitter"></i></a>
                        <a href="${buildShareUrl('whatsapp', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon wa" aria-label="Partager sur WhatsApp"><i class="fab fa-whatsapp"></i></a>
                    </div>

                    ${closeBtn ? `<div class="ws-card-owner-action">${closeBtn}</div>` : ''}
                </div>
            </article>
        </div>
    `;
}

function GenerateFundingRequestList(response) {
    $('#pagination').empty();
    $('#results-count').text(`${response.pagination.total_elements} demande(s) trouvee(s)`);

    if (response.funding_requests.length === 0) {
        $('#fundings-container').append(`
            <div class="empty-state">
                <i class="material-icons empty-state-icon">search_off</i>
                <h5>Aucune demande de financement a afficher</h5>
                <p>Essayez de modifier vos filtres ou revenez plus tard.</p>
            </div>
        `);
        $('#loader').hide();
        return;
    }

    response.funding_requests.forEach(function (fundingRequest, index) {
        $('#fundings-container').append(renderFundingCard(fundingRequest, index));
    });

>>>>>>> chore/security-design-hardening
    if (response.pagination.has_previous) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page - 1}">Precedent
                               <i class="material-icons left">chevron_left</i>
                           </button>`);
    }
    $('#pagination').append(`<span>&nbsp;&nbsp;Page ${response.pagination.current_page} sur ${response.pagination.total_pages}</span>`);
    if (response.pagination.has_next) {
<<<<<<< HEAD
        $('#pagination').append(` <button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
=======
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
>>>>>>> chore/security-design-hardening
                               <i class="material-icons right">chevron_right</i>
                           </button>`);
    }
}

$(document).ready(function () {
<<<<<<< HEAD

    // Fonction pour charger les éléments avec pagination
    function loadFundingRequests(page = 1, itemsPerPage = 9) {
        // Afficher le loader
        $('#loader').show();

        // Utiliser la balise {% url %} pour générer l'URL dynamique
        const apiUrl = "/api/funding-requests/?page=" + page + "&items_per_page=" + itemsPerPage;

        formData = $('#filterForm').serialize()


        $.ajax({
            url: apiUrl, // Appel à l'API avec paramètres de pagination
=======
    function loadFundingRequests(page = 1) {
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#fundings-container', itemsPerPage > 9 ? 8 : 6);

        const apiUrl = `/api/funding-requests/?page=${page}&items_per_page=${itemsPerPage}`;
        const formData = $('#filterForm').serialize();

        $.ajax({
            url: apiUrl,
>>>>>>> chore/security-design-hardening
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function (response) {
<<<<<<< HEAD
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
=======
                $('#loader').hide();
                $('#fundings-container').empty();
                GenerateFundingRequestList(response);
            },
            error: function (xhr, status, error) {
                $('#loader').hide();
                $('#fundings-container').empty();
                $('#results-count').text('');
                $('#fundings-container').append(`
                    <div class="error-state">
                        <i class="material-icons error-state-icon">cloud_off</i>
                        <h5>Erreur lors du chargement des demandes de financement</h5>
                        <p>Verifiez votre connexion internet et reessayez.</p>
                        <button class="btn waves-effect waves-light red darken-1" onclick="location.reload()">
                            <i class="material-icons left">refresh</i> Reessayer
                        </button>
                    </div>
                `);
                console.error('Erreur lors du chargement des elements : ', error);
>>>>>>> chore/security-design-hardening
            }
        });
    }

<<<<<<< HEAD
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
=======
    loadFundingRequests();

    $('#pagination').on('click', '.btn-page', function () {
        const page = $(this).data('page');
        loadFundingRequests(page);
        $('html, body').animate({ scrollTop: $('#fundings-container').offset().top - 80 }, 400);
    });

    $('#filterForm').submit(function (event) {
        event.preventDefault();
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#fundings-container', itemsPerPage > 9 ? 8 : 6);

        let formData = $(this).serializeArray();

>>>>>>> chore/security-design-hardening
        formData = formData.map(field => {
            if (field.name === 'start_date' || field.name === 'end_date') {
                field.value = convertToSQLDate(field.value);
            }
            return field;
        });

<<<<<<< HEAD
        // Transformation en objet URL-encoded
        const encodedData = $.param(formData);

        const page = 1;
        const itemsPerPage = 9;
        const apiUrl = `/api/funding-requests/?page=${page}&items_per_page=${itemsPerPage}`;

        $('#fundings-container').empty();
        console.log("Data", encodedData);

        // Envoie une requête AJAX
=======
        const encodedData = $.param(formData);
        const apiUrl = `/api/funding-requests/?page=1&items_per_page=${itemsPerPage}`;

>>>>>>> chore/security-design-hardening
        $.ajax({
            url: apiUrl,
            type: 'GET',
            data: encodedData,
            success: function (response) {
                $('#loader').hide();
<<<<<<< HEAD
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
=======
                $('#fundings-container').empty();
                GenerateFundingRequestList(response);
            },
            error: function () {
                $('#loader').hide();
                $('#fundings-container').empty();
                $('#results-count').text('');
                $('#fundings-container').append(`
                    <div class="error-state">
                        <i class="material-icons error-state-icon">cloud_off</i>
                        <h5>Erreur lors du chargement des demandes de financement</h5>
                        <p>Verifiez votre connexion internet et reessayez.</p>
                        <button class="btn waves-effect waves-light red darken-1" onclick="location.reload()">
                            <i class="material-icons left">refresh</i> Reessayer
                        </button>
                    </div>
                `);
>>>>>>> chore/security-design-hardening
            }
        });
    });

<<<<<<< HEAD
// Fonction de conversion
=======
>>>>>>> chore/security-design-hardening
    function convertToSQLDate(dateStr) {
        if (!dateStr) return '';
        const [day, month, year] = dateStr.split('-');
        if (!day || !month || !year) return '';
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }

<<<<<<< HEAD


});
=======
    $(document).on('click', '.close-btn', function (e) {
        e.preventDefault();
        const btn = $(this);
        const closeUrl = btn.data('close-url');

        $.ajax({
            url: closeUrl,
            type: 'POST',
            headers: {
                'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken')
            },
            success: function () {
                M.toast({ html: 'Demande cloturee avec succes.', classes: 'green' });
                loadFundingRequests(1);
            },
            error: function (xhr) {
                let errorMsg = 'Erreur lors de la cloture.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Vous n etes pas autorise a cloturer cette demande.';
                }
                M.toast({ html: errorMsg, classes: 'red' });
            }
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === `${name}=`) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
>>>>>>> chore/security-design-hardening
