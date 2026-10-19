/**
 * SOS Guinée - Popup d'aperçu universel pour Images, PDF et Word
 * Permet d'afficher en grand par simple clic :
 * - Images (.jpg, .png, .webp, .gif)
 * - Documents PDF (.pdf) via visionneuse intégrée
 * - Documents Word (.docx, .doc) avec rendu interactif et options de consultation
 */
(function () {
  'use strict';

  var DOCX_PREVIEW_CDN = 'https://cdn.jsdelivr.net/npm/docx-preview@0.3.3/dist/docx-preview.min.js';
  var isDocxScriptLoading = false;
  var isDocxScriptLoaded = false;

  function loadDocxScript(callback) {
    if (window.docx) {
      isDocxScriptLoaded = true;
      callback(true);
      return;
    }
    if (isDocxScriptLoaded) {
      callback(true);
      return;
    }
    if (isDocxScriptLoading) {
      var checkInterval = setInterval(function () {
        if (window.docx) {
          clearInterval(checkInterval);
          callback(true);
        }
      }, 100);
      return;
    }

    isDocxScriptLoading = true;
    var script = document.createElement('script');
    script.src = DOCX_PREVIEW_CDN;
    script.async = true;
    script.onload = function () {
      isDocxScriptLoaded = true;
      isDocxScriptLoading = false;
      callback(true);
    };
    script.onerror = function () {
      isDocxScriptLoading = false;
      callback(false);
    };
    document.head.appendChild(script);
  }

  function getFileExtension(url) {
    if (!url) return '';
    try {
      var clean = url.split('#')[0].split('?')[0];
      var parts = clean.split('.');
      return parts.length > 1 ? parts.pop().toLowerCase() : '';
    } catch (e) {
      return '';
    }
  }

  function initPreviewModal() {
    var modal = document.getElementById('sg-image-preview-modal');
    if (!modal) return;

    var backdrop = modal.querySelector('.sg-preview-backdrop');
    var closeBtn = modal.querySelector('.sg-preview-close-btn');
    var externalBtn = document.getElementById('sg-preview-external-btn');
    var downloadBtn = document.getElementById('sg-preview-download-btn');
    var badge = document.getElementById('sg-preview-modal-type-badge');
    var captionEl = document.getElementById('sg-preview-modal-caption');

    var previewImg = document.getElementById('sg-preview-modal-img');
    var previewIframe = document.getElementById('sg-preview-modal-iframe');
    var previewDocx = document.getElementById('sg-preview-modal-docx');
    var previewFallback = document.getElementById('sg-preview-modal-fallback');

    var fallbackTitle = document.getElementById('sg-fallback-title');
    var fallbackIcon = document.getElementById('sg-fallback-icon');
    var fallbackDownload = document.getElementById('sg-fallback-download-btn');
    var fallbackOffice = document.getElementById('sg-fallback-office-btn');

    var isClosing = false;
    var previousFocusedElement = null;

    function resetViews() {
      if (previewImg) {
        previewImg.style.display = 'none';
        previewImg.src = '';
      }
      if (previewIframe) {
        previewIframe.style.display = 'none';
        previewIframe.src = '';
      }
      if (previewDocx) {
        previewDocx.style.display = 'none';
        previewDocx.innerHTML = '';
      }
      if (previewFallback) {
        previewFallback.style.display = 'none';
      }
    }

    function openModal(src, caption, forcedType) {
      if (!src) return;
      previousFocusedElement = document.activeElement;
      resetViews();

      var ext = forcedType || getFileExtension(src);
      var isPdf = (ext === 'pdf');
      var isWord = (ext === 'docx' || ext === 'doc');
      var isImg = (!isPdf && !isWord);

      // Met à jour la légende et les boutons de tête
      var displayCaption = caption || src.split('/').pop() || 'Document';
      if (captionEl) captionEl.textContent = displayCaption;

      if (externalBtn) {
        externalBtn.href = src;
      }
      if (downloadBtn) {
        downloadBtn.href = src;
        downloadBtn.setAttribute('download', displayCaption);
      }

      // Configuration selon le type
      if (isPdf) {
        // Mode PDF : Iframe plein écran
        if (badge) {
          badge.textContent = 'PDF';
          badge.className = 'sg-preview-badge badge-pdf';
        }
        if (previewIframe) {
          previewIframe.src = src + '#toolbar=1&navpanes=0';
          previewIframe.style.display = 'block';
        }
      } else if (isWord) {
        // Mode Word (.docx ou .doc)
        if (badge) {
          badge.textContent = ext.toUpperCase();
          badge.className = 'sg-preview-badge badge-word';
        }

        if (fallbackTitle) fallbackTitle.textContent = displayCaption;
        if (fallbackDownload) fallbackDownload.href = src;

        // Lien Office Viewer si URL http(s) publique
        var isHttp = src.indexOf('http://') === 0 || src.indexOf('https://') === 0;
        var isLocal = src.indexOf('localhost') !== -1 || src.indexOf('127.0.0.1') !== -1;
        if (fallbackOffice) {
          if (isHttp && !isLocal) {
            fallbackOffice.href = 'https://view.officeapps.live.com/op/view.aspx?src=' + encodeURIComponent(src);
            fallbackOffice.style.display = 'inline-flex';
          } else {
            fallbackOffice.style.display = 'none';
          }
        }

        if (ext === 'docx' && previewDocx) {
          // Affiche message de chargement
          previewDocx.style.display = 'block';
          previewDocx.innerHTML = '<div class="sg-docx-loading"><i class="material-icons rotating">sync</i><span>Chargement du document Word...</span></div>';

          loadDocxScript(function (ok) {
            if (!ok || !window.docx) {
              previewDocx.style.display = 'none';
              if (previewFallback) previewFallback.style.display = 'flex';
              return;
            }

            fetch(src)
              .then(function (res) {
                if (!res.ok) throw new Error('HTTP ' + res.status);
                return res.blob();
              })
              .then(function (blob) {
                previewDocx.innerHTML = '';
                return window.docx.renderAsync(blob, previewDocx, null, {
                  className: 'docx-rendered',
                  inWrapper: true,
                  ignoreWidth: false,
                  ignoreHeight: false
                });
              })
              .catch(function (err) {
                console.warn('Docx preview fallback:', err);
                previewDocx.style.display = 'none';
                if (previewFallback) previewFallback.style.display = 'flex';
              });
          });
        } else {
          // .doc binaire ou autre : carte de téléchargement et options
          if (previewFallback) previewFallback.style.display = 'flex';
        }
      } else {
        // Mode Image
        if (badge) {
          badge.textContent = 'IMAGE';
          badge.className = 'sg-preview-badge badge-img';
        }
        if (previewImg) {
          previewImg.src = src;
          previewImg.alt = displayCaption;
          previewImg.style.display = 'block';
        }
      }

      modal.style.display = 'flex';
      modal.setAttribute('aria-hidden', 'false');

      // Bloquer le scroll
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';

      requestAnimationFrame(function () {
        modal.classList.add('is-open');
        if (closeBtn) closeBtn.focus();
      });
    }

    function closeModal() {
      if (isClosing) return;
      isClosing = true;

      modal.classList.remove('is-open');
      modal.setAttribute('aria-hidden', 'true');

      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';

      setTimeout(function () {
        modal.style.display = 'none';
        resetViews();
        isClosing = false;
        if (previousFocusedElement && typeof previousFocusedElement.focus === 'function') {
          previousFocusedElement.focus();
        }
      }, 260);
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        closeModal();
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', function (e) {
        e.preventDefault();
        closeModal();
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) {
        closeModal();
      }
    });

    // Délégation d'événements pour tous les déclencheurs d'aperçu
    document.addEventListener('click', function (e) {
      var target = e.target.closest('.custom-previewable, [data-custom-preview], .document-preview-card');
      if (!target) return;

      // Si l'utilisateur clique sur un bouton de téléchargement explicite, on laisse faire
      if (e.target.closest('a[download], .btn-download')) return;

      e.preventDefault();
      e.stopPropagation();

      var src = target.getAttribute('data-full-image') ||
                target.getAttribute('data-document-url') ||
                target.getAttribute('href') ||
                target.currentSrc ||
                target.src;

      var caption = target.getAttribute('data-caption') ||
                    target.getAttribute('data-title') ||
                    target.alt ||
                    target.getAttribute('title') ||
                    '';

      var type = target.getAttribute('data-document-type') || '';

      openModal(src, caption, type);
    });

    window.SGImagePreview = {
      open: openModal,
      close: closeModal
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPreviewModal);
  } else {
    initPreviewModal();
  }
})();
