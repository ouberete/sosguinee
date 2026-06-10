document.addEventListener("DOMContentLoaded", function () {
  const formatGNF = (value) => {
    const normalized = Number(value || 0);
    if (!Number.isFinite(normalized) || normalized <= 0) return "";
    return `${Math.round(normalized).toLocaleString("fr-FR")} GNF`;
  };

  const parseNumeric = (value) => {
    if (typeof value === "number") return value;
    const normalized = String(value || "").trim().replace(/\s/g, "").replace(",", ".");
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const roundDown = (value, step) => {
    if (!Number.isFinite(value) || value <= 0) return 0;
    return Math.floor(value / step) * step;
  };

  const uniqueSorted = (values) => {
    const set = new Set(values.filter((v) => Number.isFinite(v) && v > 0));
    return Array.from(set).sort((a, b) => a - b);
  };

  const selectableAmounts = [10000, 50000, 100000, 500000, 1000000, 10000000];

  const buildFundingPresets = (remaining, minAmount, step) => {
    const presets = selectableAmounts
      .filter((amount) => amount <= remaining)
      .map((amount) => roundDown(amount, step));

    const normalized = uniqueSorted(presets).filter((amount) => amount >= minAmount && amount <= remaining);
    if (!normalized.length && remaining > 0) {
      normalized.push(Math.max(1, roundDown(remaining, step)));
    }
    return normalized;
  };

  const buildDonationPresets = (minAmount, step) => {
    return uniqueSorted(selectableAmounts.map((amount) => roundDown(amount, step))).filter(
      (amount) => amount >= minAmount
    );
  };

  document.querySelectorAll(".amount-presets").forEach((container) => {
    const form = container.closest("form");
    if (!form) return;

    const amountInput = form.querySelector("input[name='amount']");
    if (!amountInput) return;

    const buttonsHost = container.querySelector(".amount-presets-buttons");
    if (!buttonsHost) return;

    let minAmount = parseInt(amountInput.getAttribute("min") || "10000", 10);
    const step = parseInt(amountInput.getAttribute("step") || "1000", 10);
    const mode = container.dataset.mode || "donation";

    let presets = [];
    if (mode === "funding") {
      const remaining = parseNumeric(container.dataset.remaining);
      if (remaining > 0) {
        amountInput.setAttribute("max", String(Math.floor(remaining)));
        minAmount = Math.min(minAmount, Math.floor(remaining));
        amountInput.addEventListener("input", function () {
          const currentValue = parseNumeric(amountInput.value);
          if (Number.isFinite(currentValue) && currentValue > remaining) {
            amountInput.value = String(Math.floor(remaining));
            if (typeof M !== "undefined" && typeof M.updateTextFields === "function") {
              M.updateTextFields();
            }
          }
        });
      }
      presets = buildFundingPresets(remaining, minAmount, step);
      if (!presets.length) {
        const fallbackAmount = Math.floor(remaining);
        if (fallbackAmount > 0) {
          presets = [fallbackAmount];
          amountInput.setAttribute("min", "1");
        } else {
          container.insertAdjacentHTML(
            "beforeend",
            "<p class='grey-text text-darken-1'>Cette collecte est déjà financée.</p>"
          );
          return;
        }
      }
    } else {
      presets = buildDonationPresets(minAmount, step);
    }

    presets.forEach((amount) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn-small waves-effect waves-light white black-text amount-preset-btn";
      button.textContent = formatGNF(amount);
      button.dataset.amountValue = String(amount);
      button.addEventListener("click", function () {
        amountInput.value = String(amount);
        amountInput.dispatchEvent(new Event("input", { bubbles: true }));
        amountInput.dispatchEvent(new Event("change", { bubbles: true }));
        amountInput.focus();
        document.querySelectorAll(".amount-preset-btn.active").forEach((activeBtn) => {
          activeBtn.classList.remove("active");
        });
        button.classList.add("active");
        if (typeof M !== "undefined" && typeof M.updateTextFields === "function") {
          M.updateTextFields();
        }
      });
      buttonsHost.appendChild(button);
    });
  });
});

