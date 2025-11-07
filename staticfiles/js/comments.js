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
                .then(data => {
                    if (data.success && data.comment_html) {
                        commentsList.insertAdjacentHTML('afterbegin', data.comment_html);
                        this.reset();
                    } else {
                        alert('Erreur: ' + (data.errors || 'Inconnue'));
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
                        alert('Commentaire signalé avec succès.');
                    } else {
                        alert('Erreur de signalement.');
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
                            commentText.textContent = newText;
                        } else {
                            alert('Erreur lors de la modification.');
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
                            const commentCard = document.getElementById(`comment-card-${commentId}`);
                            if (commentCard) commentCard.remove();
                        } else {
                            alert('Erreur lors de la suppression.');
                        }
                    });
            }
        }
    });

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});