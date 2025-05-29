$(document).ready(function(){
    
    //Remove css loader
    $('#overlay').removeClass('loading');
    var csrftoken = $('input[name=csrfmiddlewaretoken]').val();
    $('#signup').submit(function(e){
        e.preventDefault();
        $('#loading-btn').attr('hidden', false);
        $('#signup-btn').attr('hidden', true);
        setTimeout(function() {
            document.getElementById('signup').submit();
        }, 100);
         });
      /*  $.ajax({ 
            type: 'POST',
            url: '/register',
            data:  {
                csrfmiddlewaretoken: csrftoken,
                // Ajoutez les autres données du formulaire
                email: $('#signup_email').val(),
                username: $('#signup_email').val(),
                password1: $('#signup_password').val(),
                password2: $('#signup_password_confirm').val(),
                civility: $('#signup_civility').val(),
                first_name: $('#signup_firstname').val(),
                last_name: $('#signup_lastname').val(),
            },
            success: function(response){
                if (response.success) {
                    window.location.href = '/account-created';
                    // Rediriger l'utilisateur vers une autre page par exemple
                } else {
                    $('#error-messages').empty();
                    $('#error-messages-2').empty();
                    $.each(response.errors, function(key, value){
                        $('#error-messages').append('<p>' + value + '</p>');
                        $('#error-messages-2').append('<p>' + value + '</p>');
                    });
                }
            },
            error: function(xhr, status, error) {
                // Gérer les erreurs AJAX ici
                $('#error-messages').text(xhr.responseText);
            }
        });
    });*/
   
    $("#loginkeeping").click(function (e) {
        //e.preventDefault();
        var x = $("#signup_password");
        var y = $("#signup_password_confirm");
        // Utilisation de toggleClass pour basculer entre les types de champ
        
        if ($(this).is(":checked")) {
            x.attr("type", "text");
            y.attr("type", "text");
        } else {
            x.attr("type", "password");
            y.attr("type", "password");
        }
    });



});

