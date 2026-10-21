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
    const goalReached = ['En cours', 'Terminé'].includes(statusLabel)
        && Number(fundingRequest.amount_received || 0) >= Number(fundingRequest.amount || 0);
    const displayStatusLabel = goalReached ? 'Collecté' : statusLabel;
    const typeLabel = fundingRequest.funding_request_type_name || 'Financement';
    const daysText = (fundingRequest.days_remaining !== null && fundingRequest.days_remaining !== undefined)
        ? `${fundingRequest.days_remaining} jours restants`
        : 'Sans echeance';
    const imgSrc = fundingRequest.principal_image_url || '/static/img/default_funding.png';
    const title = escapeHtml(fundingRequest.title || 'Demande de financement');
    const beneficiaryName = escapeHtml(fundingRequest.beneficiary_name || 'Beneficiaire');
    const description = escapeHtml(truncateText(fundingRequest.description_needs || 'Aucune description disponible.', 160));
    const collectedAmount = formatCurrency(fundingRequest.amount_received || 0);
    const targetAmount = formatCurrency(fundingRequest.amount || 0);
    const fullUrl = `${window.location.origin}${fundingRequest.details_url}`;
    const paymentUrl = fundingRequest.payment_url || `/funding/${fundingRequest.public_id}/djomy/`;
    const canFund = fundingRequest.can_fund === true
        || statusLabel === 'En cours'
        || (statusLabel === 'Terminé' && goalReached);
    const shareTitle = `Aide ${fundingRequest.beneficiary_name} - ${fundingRequest.title} - Ensemble 224`;
    const animDelay = `animation-delay: ${index * 0.07}s`;
    const statusClass = goalReached
        ? 'status-open'
        : getStatusClass(displayStatusLabel, fundingRequest.days_remaining, fundingRequest.progress);
    const progressClass = getProgressClass(fundingRequest.progress);

    const closeBtn = fundingRequest.is_creator && !isClosedStatus(displayStatusLabel)
        ? `<button class="btn waves-effect waves-light grey darken-1 close-btn" data-public-id="${fundingRequest.public_id}" data-close-url="${fundingRequest.close_url}" onclick="return confirm('Voulez-vous vraiment cloturer cette demande de financement ?')">
                <i class="material-icons left">check_circle</i> Cloturer
           </button>`
        : '';

    const initials = (fundingRequest.beneficiary_name || 'BE')
        .split(' ')
        .map(n => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase();

    const progressValue = fundingRequest.progress_percentage ?? Math.round(fundingRequest.progress || 0);

    return `
        <div class="col s12 m6 l4 card-animate" style="${animDelay}">
            <article class="ws-card ws-funding-card" role="article" aria-labelledby="fund-title-${fundingRequest.id}">
                <div class="ws-card-image-wrap">
                    <a class="ws-card-image image-loading-frame" href="${fundingRequest.details_url}" aria-label="Voir ${title}">
                        <img data-image-loading data-image-fallback="/static/img/default_funding.png" src="${imgSrc}" alt="${beneficiaryName}" loading="lazy">
                    </a>
                    <span class="ws-card-badge-type">
                        <i class="material-icons">category</i> ${escapeHtml(typeLabel)}
                    </span>
                    <span class="ws-card-badge-status ${statusClass}">
                        <i class="material-icons">bolt</i> ${escapeHtml(displayStatusLabel)}
                    </span>
                </div>

                <div class="ws-card-body">
                    <h3 id="fund-title-${fundingRequest.id}" class="ws-card-title">
                        <a href="${fundingRequest.details_url}">${title}</a>
                    </h3>

                    <div class="ws-card-amount-block">
                        <span class="ws-card-amount-big">${collectedAmount}</span>
                        <span class="ws-card-amount-sub">collectés sur ${targetAmount}</span>
                    </div>

                    <div class="ws-card-progress">
                        <div class="ws-card-progress-track" role="progressbar" aria-valuenow="${fundingRequest.progress}" aria-valuemin="0" aria-valuemax="100">
                            <div class="ws-card-progress-fill ${progressClass}" style="width: ${fundingRequest.progress}%"></div>
                        </div>
                        <div class="ws-card-progress-meta">
                            <span class="ws-card-progress-percent">${progressValue}% atteint</span>
                            <span>${daysText}</span>
                        </div>
                        ${Number(fundingRequest.excess_amount || 0) > 0
                            ? `<p class="funding-over-target-note">Objectif dépassé de ${formatCurrency(fundingRequest.excess_amount)} GNF</p>`
                            : ''}
                    </div>

                    <p class="ws-card-desc">${description}</p>

                    <div class="ws-card-action">
                        ${canFund
                            ? `<a href="${paymentUrl}" class="btn ws-card-cta waves-effect waves-light" aria-label="Financer ${title}">
                                 <i class="material-icons left">payments</i> Financer
                               </a>`
                            : `<a id="${fundingRequest.id}-funddetails" href="${fundingRequest.details_url}" class="btn ws-card-cta ws-card-cta--secondary waves-effect" aria-label="Voir détails ${title}">
                                 Voir détails
                               </a>`
                        }
                    </div>

                    <div class="ws-card-footer">
                        <div class="ws-card-publisher">
                            <div class="ws-card-publisher-avatar" aria-hidden="true">${escapeHtml(initials)}</div>
                            <div class="ws-card-publisher-info">
                                <span class="ws-card-publisher-sub">Bénéficiaire</span>
                                <span class="ws-card-publisher-name">${beneficiaryName}</span>
                            </div>
                        </div>

                        <div class="ws-card-socials">
                            <a href="${buildShareUrl('whatsapp', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon wa" aria-label="Partager sur WhatsApp"><i class="fab fa-whatsapp"></i></a>
                            <a href="${buildShareUrl('facebook', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon fb" aria-label="Partager sur Facebook"><i class="fab fa-facebook-f"></i></a>
                        </div>
                    </div>

                    ${closeBtn ? `<div class="ws-card-owner-action" style="margin-top: 10px;">${closeBtn}</div>` : ''}
                </div>
            </article>
        </div>
    `;
}

function GenerateFundingRequestList(response) {
    $('#pagination').empty();
    $('#results-count').text(`${response.pagination.total_elements} demande(s) trouvée(s)`);

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

    if (response.pagination.has_previous) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page - 1}">Precedent
                               <i class="material-icons left">chevron_left</i>
                           </button>`);
    }
    $('#pagination').append(`<span>&nbsp;&nbsp;Page ${response.pagination.current_page} sur ${response.pagination.total_pages}</span>`);
    if (response.pagination.has_next) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
                               <i class="material-icons right">chevron_right</i>
                           </button>`);
    }
}

$(document).ready(function () {
    function loadFundingRequests(page = 1) {
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#fundings-container', itemsPerPage > 9 ? 8 : 6);

        const apiUrl = `/api/funding-requests/?page=${page}&items_per_page=${itemsPerPage}`;
        const formData = $('#filterForm').serialize();

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
            }
        });
    }

    loadFundingRequests();

    $('#pagination').on('click', '.btn-page', function () {
        const page = $(this).data('page');
        loadFundingRequests(page);
        $('html, body').animate({ scrollTop: $('#fundings-container').offset().top - 80 }, 400);
    });

    // Empêcher la propagation des clics sur les select-wrapper pour éviter les sauts de scroll
    $(document).on('click', '.select-wrapper', function (e) {
        e.stopPropagation();
    });

    // Filtre réactif au changement d'un select
    $('#filterForm select').on('change', function () {
        $('#filterForm').submit();
    });

    $('#filterForm').submit(function (event) {
        event.preventDefault();
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#fundings-container', itemsPerPage > 9 ? 8 : 6);

        let formData = $(this).serializeArray();

        formData = formData.map(field => {
            if (field.name === 'start_date' || field.name === 'end_date') {
                field.value = convertToSQLDate(field.value);
            }
            return field;
        });

        const encodedData = $.param(formData);
        const apiUrl = `/api/funding-requests/?page=1&items_per_page=${itemsPerPage}`;

        $.ajax({
            url: apiUrl,
            type: 'GET',
            data: encodedData,
            success: function (response) {
                $('#loader').hide();
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
            }
        });
    });

    function convertToSQLDate(dateStr) {
        if (!dateStr) return '';
        const [day, month, year] = dateStr.split('-');
        if (!day || !month || !year) return '';
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }

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
