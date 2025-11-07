/* Submit contact form with ajax */
$(document).ready(function(){
    var csrftoken = $('input[name=csrfmiddlewaretoken]').val();
    var isSubmitting = false;

    $('#contact-form').submit(function(e){
        e.preventDefault();
        if (isSubmitting) return;

        isSubmitting = true;
        $("#message-error").text("");
        $("#message-success").text("");
        $("#loader-2").attr('style', 'display: block !important;');
        $("#loader").attr('style', 'display: block !important;');
        var name = $('#name').val();
        var email = $('#email').val();
        var message = $('#message').val();
        
        $.ajax({
            type: 'POST',
            url: '/contact-2/',
            data:  {
                csrfmiddlewaretoken: csrftoken,
                name: name,
                email: email,
                message: message
            },
            success: function(response){
                $("#loader-2").attr('style', 'display: none !important;');
                $("#loader").attr('style', 'display: none !important;');
                isSubmitting = false;

                // Hide any existing toasts before showing a new one
                M.Toast.dismissAll();

                if (response.success) {
                    $("#message-success").text(response.success);
                    M.toast({
                        html: response.success,
                        displayLength: 5000,
                        classes: 'toast-success'
                    });
                    /* vider les champs */
                    $("#contact-form")[0].reset();

                } else if(response.error) {
                    $('#message-error').text(response.error);
                    console.log("Error data", response.error);
                    M.toast({html: response.error, displayLength: 5000, classes: 'toast-error'});
                } else {
                    $('#message-error').text("Erreur survenue, veuillez réessayer");
                    M.toast({html:"Erreur survenue, veuillez réessayer", displayLength: 5000, classes: 'toast-error'});
                }
            },
            error: function (data) {
                $("#loader-2").attr('style', 'display: none !important;');
                $("#loader").attr('style', 'display: none !important;');
                isSubmitting = false;

                // Hide any existing toasts before showing a new one
                M.Toast.dismissAll();

                $("#message-error").html(data.error);
                console.log(data);
                M.toast({html: data.error, displayLength: 5000, classes: 'toast-error'});
            }
        });
    });
})

function showLoader(event) {
    event.preventDefault();
    /*Verifier le formulaire est valide avant d'afficher le loader de soumission*/

    var form = document.getElementById('contact');
    if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
        form.classList.add('was-validated');
        M.toast({html: "Veuillez remplir correctement le formulaire", displayLength: 5000, classes: 'toast-error'});
        return;
    }
    document.getElementById('loader').style.display = 'block';
    form.submit();
}

function submitContactForm() {
    e.preventDefault();
    alert("Yes I did it !!")
    var csrftoken = $('input[name=csrfmiddlewaretoken]').val();
    
    /*recuperer les données du formulaire*/
    var form = document.getElementById('contact-form');
    var formData = new FormData(form);

    formData.append('csrfmiddlewaretoken', csrftoken);

    

    /*Afficher les données du formulaire*/
    console.log("Data: ",formData);
    console.log("form",form);
    alert("End")

    setTimeout(function(){ alert("Hello"); }, 10000);
    alert("Hello 2")
  
    $.ajax({
        type: 'POST',
        url: '/contact',
        data: formData,
        success: function (data) {
            console.log(data);
        },
        error: function (data) {
            console.log(data);
        },
        cache: false,
        contentType: false,
        processData: false
    });
}