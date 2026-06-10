document.addEventListener("DOMContentLoaded", function () {
  const formatSize = (value) => {
    const bytes = Number(value || 0);
    if (!Number.isFinite(bytes) || bytes <= 0) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const toArray = (fileList) => Array.from(fileList || []);

  const supportsDataTransfer = () => typeof DataTransfer !== "undefined";

  const setInputFiles = (input, files) => {
    if (!supportsDataTransfer()) return false;
    const transfer = new DataTransfer();
    files.forEach((file) => transfer.items.add(file));
    input.files = transfer.files;
    return true;
  };

  const makePreviewEmpty = (preview, label) => {
    preview.innerHTML = `<p class="upload-preview-empty">${label}</p>`;
  };

  const renderImagePreview = (preview, file, removeHandler) => {
    preview.innerHTML = "";
    const card = document.createElement("div");
    card.className = "upload-preview-card upload-preview-image-card";

    const img = document.createElement("img");
    img.alt = file.name;
    img.className = "upload-preview-image";
    const reader = new FileReader();
    reader.onload = (event) => {
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);

    const meta = document.createElement("div");
    meta.className = "upload-preview-meta";
    meta.innerHTML = `<strong>${file.name}</strong><span>${formatSize(file.size)}</span>`;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "upload-preview-remove";
    remove.textContent = "Retirer";
    remove.addEventListener("click", removeHandler);

    card.appendChild(img);
    card.appendChild(meta);
    card.appendChild(remove);
    preview.appendChild(card);
  };

  const renderDocsPreview = (preview, files, removeHandlerFactory) => {
    preview.innerHTML = "";
    if (!files.length) {
      makePreviewEmpty(preview, "Aucun fichier sélectionné");
      return;
    }

    files.forEach((file, index) => {
      const item = document.createElement("div");
      item.className = "upload-preview-card upload-preview-file-card";

      const icon = document.createElement("i");
      icon.className = "material-icons upload-preview-icon";
      icon.textContent = file.type && file.type.startsWith("image/") ? "image" : "description";

      const meta = document.createElement("div");
      meta.className = "upload-preview-meta";
      meta.innerHTML = `<strong>${file.name}</strong><span>${formatSize(file.size)}</span>`;

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "upload-preview-remove";
      remove.textContent = "Retirer";
      remove.addEventListener("click", removeHandlerFactory(index));

      item.appendChild(icon);
      item.appendChild(meta);
      item.appendChild(remove);
      preview.appendChild(item);
    });
  };

  document.querySelectorAll("[data-upload-zone]").forEach((zone) => {
    const field = zone.closest(".upload-field");
    if (!field) return;

    const input = field.querySelector("input[type='file']");
    const preview = field.querySelector("[data-upload-preview]");
    const action = field.querySelector("[data-upload-action]");
    if (!input || !preview) return;

    const isMultiple = input.hasAttribute("multiple");
    let currentFiles = [];

    const updateAction = () => {
      if (!action) return;
      const icon = action.querySelector("i");
      const label = action.querySelector("em");
      const hasFiles = currentFiles.length > 0;

      if (isMultiple) {
        if (icon) icon.textContent = "add_circle";
        if (label) label.textContent = hasFiles ? "Ajouter" : "Ajouter";
        action.dataset.state = hasFiles ? "filled" : "empty";
        return;
      }

      if (hasFiles) {
        if (icon) icon.textContent = "edit";
        if (label) label.textContent = "Remplacer";
        action.dataset.state = "filled";
      } else {
        if (icon) icon.textContent = "add_photo_alternate";
        if (label) label.textContent = "Ajouter";
        action.dataset.state = "empty";
      }
    };

    const sync = () => {
      if (!currentFiles.length) {
        input.value = "";
        updateAction();
        return;
      }
      setInputFiles(input, currentFiles);
      updateAction();
    };

    const refresh = () => {
      if (!currentFiles.length) {
        makePreviewEmpty(preview, "Aucun fichier sélectionné");
        updateAction();
        return;
      }

      if (isMultiple) {
        renderDocsPreview(preview, currentFiles, (index) => () => {
          currentFiles = currentFiles.filter((_, idx) => idx !== index);
          sync();
          refresh();
        });
      } else {
        renderImagePreview(preview, currentFiles[0], () => {
          currentFiles = [];
          sync();
          refresh();
        });
      }
      updateAction();
    };

    const setFiles = (files, append = false) => {
      const nextFiles = toArray(files).filter(Boolean);
      if (!nextFiles.length) return;

      if (isMultiple) {
        currentFiles = append ? currentFiles.concat(nextFiles) : nextFiles;
      } else {
        currentFiles = [nextFiles[0]];
      }

      sync();
      refresh();
    };

    input.addEventListener("change", () => {
      setFiles(input.files, isMultiple);
    });

    if (action) {
      action.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        input.click();
      });
    }

    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("is-dragover");
    });

    zone.addEventListener("dragleave", () => {
      zone.classList.remove("is-dragover");
    });

    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      zone.classList.remove("is-dragover");
      const droppedFiles = toArray(event.dataTransfer && event.dataTransfer.files);
      if (!droppedFiles.length) return;
      setFiles(droppedFiles, isMultiple);
    });

    refresh();
  });
});
