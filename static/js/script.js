document.addEventListener('DOMContentLoaded', function() {
    const radios = document.querySelectorAll('input[name="amount"]');
    const autreMontantInput = document.getElementById('other_amount');
    console.log(autreMontantInput);
    console.log(radios);
    radios.forEach(radio => {
      radio.addEventListener('change', function() {
        autreMontantInput.value = '';
        alert('test');
        if (this.value === 'other') {
          autreMontantInput.disabled = false;
        } else {
          autreMontantInput.disabled = true;
        }
      });
    });
  });