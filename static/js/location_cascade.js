document.addEventListener("DOMContentLoaded", function () {
  if (typeof M !== "undefined") {
    M.FormSelect.init(document.querySelectorAll("select"));
    if (typeof M.updateTextFields === "function") {
      M.updateTextFields();
    }
  }

  const forms = document.querySelectorAll("form[data-location-cascade='true']");
  forms.forEach((form) => {
    const regionSel = form.querySelector("#id_region");
    const prefSel = form.querySelector("#id_prefecture");
    const comSel = form.querySelector("#id_commune");
    const quaSel = form.querySelector("#id_quarter");
    const submitBtn = form.querySelector("button[type='submit']");

    const refreshSelect = (select) => {
      if (!select || typeof M === "undefined") return;
      const instance = M.FormSelect.getInstance(select);
      if (instance) instance.destroy();
      M.FormSelect.init(select);
    };

    const initSelect = (select, placeholder) => {
      if (!select) return;
      if (!select.value) {
        select.innerHTML = "";
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = placeholder;
        opt.disabled = true;
        opt.selected = true;
        select.appendChild(opt);
      }
      refreshSelect(select);
    };

    const populateSelect = (select, items, placeholder) => {
      if (!select) return;
      const previousValue = select.value;
      refreshSelect(select);
      select.innerHTML = "";
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = placeholder;
      opt.disabled = true;
      opt.selected = true;
      select.appendChild(opt);
      items.forEach((item) => {
        const option = document.createElement("option");
        option.value = item.id;
        option.textContent = item.name;
        if (String(item.id) === String(previousValue)) {
          option.selected = true;
          opt.selected = false;
        }
        select.appendChild(option);
      });
      refreshSelect(select);
    };

    const fetchJSON = async (url) => {
      try {
        const response = await fetch(url, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!response.ok) return { results: [] };
        return await response.json();
      } catch (_error) {
        return { results: [] };
      }
    };

    initSelect(prefSel, "Sélectionnez une préfecture");
    initSelect(comSel, "Sélectionnez une commune");
    initSelect(quaSel, "Sélectionnez un quartier");

    if (regionSel && prefSel && comSel && quaSel) {
      regionSel.addEventListener("change", async function () {
        const region = this.value;
        populateSelect(prefSel, [], "Sélectionnez une préfecture");
        populateSelect(comSel, [], "Sélectionnez une commune");
        populateSelect(quaSel, [], "Sélectionnez un quartier");
        if (region) {
          const data = await fetchJSON(
            `/api/locations/prefectures/?region=${encodeURIComponent(region)}`
          );
          populateSelect(prefSel, data.results || [], "Sélectionnez une préfecture");
        }
      });

      prefSel.addEventListener("change", async function () {
        const pref = this.value;
        populateSelect(comSel, [], "Sélectionnez une commune");
        populateSelect(quaSel, [], "Sélectionnez un quartier");
        if (pref) {
          const data = await fetchJSON(
            `/api/locations/communes/?prefecture=${encodeURIComponent(pref)}`
          );
          populateSelect(comSel, data.results || [], "Sélectionnez une commune");
        }
      });

      comSel.addEventListener("change", async function () {
        const com = this.value;
        populateSelect(quaSel, [], "Sélectionnez un quartier");
        if (com) {
          const data = await fetchJSON(
            `/api/locations/quarters/?commune=${encodeURIComponent(com)}`
          );
          populateSelect(quaSel, data.results || [], "Sélectionnez un quartier");
        }
      });
    }

    if (submitBtn) {
      form.addEventListener("submit", function () {
        submitBtn.disabled = true;
        submitBtn.classList.add("disabled");
      });
    }
  });
});
