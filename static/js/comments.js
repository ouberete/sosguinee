function initDropdowns() {
    const dropdownElems = document.querySelectorAll('.dropdown-trigger');
    M.Dropdown.init(dropdownElems, {
        constrainWidth: false,
        coverTrigger: false,
        alignment: 'right',
        closeOnClick: true
    });
}

// Call this after comments are loaded/updated
document.addEventListener('DOMContentLoaded', function() {
    initDropdowns();
});


// Fermer tous les dropdowns si on clique ailleurs
document.addEventListener('DOMContentLoaded', function () {
    function showToast(message, classes = '') {
        if (window.M && M.toast) {
            M.toast({ html: message, classes, displayLength: 3000 });
        } else {
            alert(message);
        }
    }
    const commentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');

    // Submit new comment
    if (commentForm) {
        commentForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const data = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': data.get('csrfmiddlewaretoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: data
            })
                .then(res => res.json())
<<<<<<< HEAD
                .then(data => {
                    if (data.success && data.comment_html) {
                        \n                        if (typeof initDropdowns === 'function') { initDropdowns(); }
=======
                    .then(data => {
                        if (data.success && data.comment_html) {
                        if (commentsList) {
                            commentsList.insertAdjacentHTML('afterbegin', data.comment_html);
                        }
                        this.reset();
                        const textarea = this.querySelector('textarea');
                        if (textarea) {
                            textarea.value = '';
                            if (window.M && M.textareaAutoResize) {
                                M.textareaAutoResize(textarea);
                            }
                        }
                        if (typeof initDropdowns === 'function') { initDropdowns(); }
>>>>>>> chore/security-design-hardening
                        showToast('Commentaire ajouté', 'green');
                    } else {
                        showToast('Erreur: ' + (data.errors || 'Inconnue'), 'red');
                    }
                });
        });
    }


    document.addEventListener('click', function(event) {
        const isDropdownButton = event.target.classList.contains('comment-menu-trigger');
        if (!isDropdownButton) {
            document.querySelectorAll('.dropdown-content').forEach(d => d.style.display = 'none');
        }
    });

    // Delegation pour actions des commentaires
    if (commentsList) {
        commentsList.addEventListener('click', function (e) {
        const target = e.target;

        // Signaler
        if (target.classList.contains('comment-report')) {
            e.preventDefault();
            const commentId = target.dataset.id;
            fetch(`/comments/${commentId}/report/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast('Commentaire signalé', 'orange');
                    } else {
                        showToast(data.error || 'Erreur de signalement', 'red');
                    }
                });
        }

        // Modifier
        if (target.classList.contains('comment-edit')) {
            const commentId = target.dataset.id;
            const commentText = document.querySelector(`#comment-text-${commentId}`);
            const newText = prompt('Modifier votre commentaire:', commentText.textContent.trim());
            if (newText) {
                fetch(`/comments/${commentId}/edit/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: newText })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
<<<<<<< HEAD
                            commentText.textContent = newText;
=======
                            commentText.textContent = newText.trim();
>>>>>>> chore/security-design-hardening
                            showToast('Commentaire modifié', 'green');
                        } else {
                            showToast('Erreur lors de la modification', 'red');
                        }
                    });
            }
        }

        // Supprimer
        if (target.classList.contains('comment-delete')) {
            const commentId = target.dataset.id;
            if (confirm('Voulez-vous vraiment supprimer ce commentaire ?')) {
                fetch(`/comments/${commentId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            const commentCard = document.getElementById(`comment-${commentId}`);
                            if (commentCard) commentCard.remove();
                            showToast('Commentaire supprimé', 'green');
                        } else {
                            showToast('Erreur lors de la suppression', 'red');
                        }
                    });
            }
        }
        });
    }

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});


