document.addEventListener('DOMContentLoaded', function () {
  // Références des éléments
  const showPasswordCheckbox = document.getElementById('show-password');
  const passwordInput = document.getElementById('password');
  const loginForm = document.getElementById('loginForm');
  const loginBtn = document.getElementById('login-btn');
  const loadingBtn = document.getElementById('loading-btn');
  const errorMessage = document.getElementById('error-message');

  // Afficher / masquer le mot de passe
  if (showPasswordCheckbox && passwordInput) {
    showPasswordCheckbox.addEventListener('change', function () {
      passwordInput.type = this.checked ? 'text' : 'password';
    });
  }

  // Soumission du formulaire
  if (loginForm) {
    loginForm.addEventListener('submit', function () {
      // Masquer les erreurs précédentes
      if (errorMessage) {
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
      }

      // Afficher le bouton de chargement
      if (loginBtn && loadingBtn) {
        loginBtn.style.display = 'none';
        loadingBtn.style.display = 'inline-block';
      }
    });
  }

  // Si une erreur a été rendue par Django, l'afficher
  if (errorMessage && errorMessage.textContent.trim() !== '') {
    errorMessage.style.display = 'block';
  }
});
