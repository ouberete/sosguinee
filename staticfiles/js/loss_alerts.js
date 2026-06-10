function convertToSQLDate(dateStr) {
    if (!dateStr) return '';
    const [day, month, year] = dateStr.split('-');
    if (!day || !month || !year) return '';
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

function getItemsPerPage() {
    const width = window.innerWidth;
    if (width >= 1400) return 12;
    if (width >= 993) return 9;
    return 6;
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

function truncateText(value, maxLength = 120) {
    if (!value) {
        return '';
    }
    return value.length > maxLength ? `${value.slice(0, maxLength - 1).trim()}...` : value;
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
    return /clos|trouve|resolu|retrouve|termine|cloture/.test(normalized);
}

function getStatusTone(statusLabel) {
    if (isClosedStatus(statusLabel)) {
        return 'bf-status-closed';
    }
    if (/urgent|critique|alerte/i.test(statusLabel)) {
        return 'bf-status-urgent';
    }
    return 'bf-status-open';
}

function buildLocation(alert) {
    const locationParts = [alert.quarter, alert.commune, alert.prefecture, alert.region].filter(Boolean);
    if (locationParts.length > 0) {
        return locationParts.join(', ');
    }
    return alert.address || 'Lieu non precise';
}

function GenerateLossAlertList(response) {
    $('#pagination').empty();
    $('#results-count').text(`${response.pagination.total_elements} alerte(s) trouvee(s)`);

    if (response.loss_alerts.length === 0) {
        $('#alerts-container').append(`
            <div class="empty-state">
                <i class="material-icons empty-state-icon">search_off</i>
                <h5>Aucune alerte a afficher</h5>
                <p>Essayez de modifier vos filtres ou revenez plus tard.</p>
            </div>
        `);
        $('#loader').hide();
        return;
    }

    response.loss_alerts.forEach(function (lossAlert, index) {
        const statusLabel = lossAlert.status_alert_name || 'En attente';
        const typeLabel = lossAlert.type_alert_name || 'Alerte';
        const imgSrc = lossAlert.principal_image_url || '/static/img/articles/img1.avif';
        const title = escapeHtml(lossAlert.name || 'Alerte de perte');
        const description = escapeHtml(truncateText(lossAlert.description || 'Signalement en attente de details complementaires.', 130));
        const fullUrl = `${window.location.origin}${lossAlert.details_url}`;
        const shareTitle = `Alerte de perte : ${lossAlert.name} - SOS Guinee`;
        const locationText = escapeHtml(buildLocation(lossAlert));
        const dateText = lossAlert.date_alert || 'Date inconnue';
        const hourText = lossAlert.hour_alert || 'Heure non precisee';
        const animDelay = `animation-delay: ${index * 0.07}s`;
        const toneClass = getStatusTone(statusLabel);

        const phoneLink = lossAlert.phone
            ? `<a href="tel:${lossAlert.phone}" class="btn-small waves-effect waves-light red lighten-1" aria-label="Contacter ${title}">
                    <i class="material-icons left">call</i> Appeler
               </a>`
            : '';

        const closeBtn = lossAlert.is_creator && !isClosedStatus(lossAlert.status_alert_name || '')
            ? `<button class="btn waves-effect waves-light grey darken-1 close-btn" data-public-id="${lossAlert.public_id}" data-close-url="${lossAlert.close_url}" onclick="return confirm('Voulez-vous vraiment cloturer cette alerte ?')">
                    <i class="material-icons left">check_circle</i> Cloturer
               </button>`
            : '';

        $('#alerts-container').append(`
            <div class="col s12 m6 l4 card-animate" style="${animDelay}">
                <article class="bf-card bf-alert-card" role="article" aria-labelledby="alert-title-${lossAlert.id}">
                    <a class="bf-card-image" href="${lossAlert.details_url}" aria-label="Voir ${title}">
                        <img src="${imgSrc}" alt="${title}" loading="lazy">
                        <span class="bf-card-badge ${toneClass}">
                            <i class="material-icons">campaign</i>
                            ${escapeHtml(statusLabel)}
                        </span>
                    </a>

                    <div class="bf-card-body">
                        <h3 id="alert-title-${lossAlert.id}" class="bf-card-title">
                            <a href="${lossAlert.details_url}">${title}</a>
                        </h3>

                        <p class="bf-card-subtitle">${escapeHtml(typeLabel)}</p>
                        <p class="bf-card-description">${description}</p>

                        <div class="bf-card-tags">
                            <span class="bf-card-tag">
                                <i class="material-icons">event</i>
                                ${escapeHtml(dateText)}
                            </span>
                            <span class="bf-card-tag">
                                <i class="material-icons">schedule</i>
                                ${escapeHtml(hourText)}
                            </span>
                            <span class="bf-card-tag">
                                <i class="material-icons">place</i>
                                ${locationText}
                            </span>
                        </div>

                        <div class="bf-card-actions">
                            <a href="${lossAlert.details_url}" id="${lossAlert.id}-dalerte" class="btn waves-effect waves-light red darken-1">
                                Voir l'alerte
                            </a>
                            ${phoneLink}
                        </div>

                        <div class="bf-card-socials">
                            <a href="${buildShareUrl('facebook', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon fb" aria-label="Partager sur Facebook"><i class="fab fa-facebook-f"></i></a>
                            <a href="${buildShareUrl('twitter', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon tw" aria-label="Partager sur Twitter"><i class="fab fa-twitter"></i></a>
                            <a href="${buildShareUrl('whatsapp', fullUrl, shareTitle)}" target="_blank" rel="noopener" class="social-icon wa" aria-label="Partager sur WhatsApp"><i class="fab fa-whatsapp"></i></a>
                        </div>

                        ${closeBtn ? `<div class="bf-card-owner-action">${closeBtn}</div>` : ''}
                    </div>
                </article>
            </div>
        `);
    });

    if (response.pagination.has_previous) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page - 1}">Precedent
                                 <i class="material-icons left">chevron_left</i></button>`);
    }
    $('#pagination').append(`<span>&nbsp;&nbsp;Page ${response.pagination.current_page} sur ${response.pagination.total_pages}</span>`);
    if (response.pagination.has_next) {
        $('#pagination').append(`<button class="btn-page btn waves-effect waves-light" data-page="${response.pagination.current_page + 1}">Suivant
                                 <i class="material-icons right">chevron_right</i></button>`);
    }
}

$(document).ready(function () {
    function loadLossAlerts(page = 1) {
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#alerts-container', itemsPerPage > 9 ? 8 : 6);

        const apiUrl = `/api/loss-alerts/?page=${page}&items_per_page=${itemsPerPage}`;
        const formData = $('#filterForm').serialize();

        $.ajax({
            url: apiUrl,
            type: 'GET',
            dataType: 'json',
            data: formData,
            success: function (response) {
                $('#loader').hide();
                $('#alerts-container').empty();
                GenerateLossAlertList(response);
            },
            error: function (xhr, status, error) {
                $('#loader').hide();
                $('#alerts-container').empty();
                $('#results-count').text('');
                $('#alerts-container').append(`
                    <div class="error-state">
                        <i class="material-icons error-state-icon">cloud_off</i>
                        <h5>Erreur lors du chargement des alertes</h5>
                        <p>Verifiez votre connexion internet et reessayez.</p>
                        <button class="btn waves-effect waves-light red darken-1" onclick="location.reload()">
                            <i class="material-icons left">refresh</i> Reessayer
                        </button>
                    </div>
                `);
                console.error('Erreur lors du chargement des alertes : ', error);
            }
        });
    }

    loadLossAlerts();

    $('#pagination').on('click', '.btn-page', function () {
        const page = $(this).data('page');
        loadLossAlerts(page);
        $('html, body').animate({ scrollTop: $('#alerts-container').offset().top - 80 }, 400);
    });

    $('#filterForm').submit(function (event) {
        event.preventDefault();
        const itemsPerPage = getItemsPerPage();
        showSkeletonLoader('#alerts-container', itemsPerPage > 9 ? 8 : 6);

        let formData = $(this).serializeArray();
        formData = formData.map(field => {
            if (field.name === 'start_date' || field.name === 'end_date') {
                field.value = convertToSQLDate(field.value);
            }
            return field;
        });

        $.ajax({
            url: `/api/loss-alerts/?page=1&items_per_page=${itemsPerPage}`,
            type: 'GET',
            data: $.param(formData),
            dataType: 'json',
            success: function (response) {
                $('#loader').hide();
                $('#alerts-container').empty();
                GenerateLossAlertList(response);
            },
            error: function () {
                $('#loader').hide();
                $('#alerts-container').empty();
                $('#results-count').text('');
                $('#alerts-container').append(`
                    <div class="error-state">
                        <i class="material-icons error-state-icon">cloud_off</i>
                        <h5>Erreur lors du chargement des alertes</h5>
                        <p>Verifiez votre connexion internet et reessayez.</p>
                        <button class="btn waves-effect waves-light red darken-1" onclick="location.reload()">
                            <i class="material-icons left">refresh</i> Reessayer
                        </button>
                    </div>
                `);
            }
        });
    });

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
                M.toast({ html: 'Alerte cloturee avec succes.', classes: 'green' });
                loadLossAlerts(1);
            },
            error: function (xhr) {
                let errorMsg = 'Erreur lors de la cloture.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Vous n etes pas autorise a cloturer cette alerte.';
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
