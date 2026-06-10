$(document).ready(function() {

    function resizeIFrameToFitContent( iFrame ) {

        iFrame.width  = iFrame.contentWindow.document.body.scrollWidth;
        iFrame.height = iFrame.contentWindow.document.body.scrollHeight;
    }
    
    window.addEventListener('DOMContentLoaded', function(e) {
    
        var iFrame = document.getElementById( 'iframe1' );
        resizeIFrameToFitContent( iFrame );
    
        // or, to resize all iframes:
        var iframes = document.querySelectorAll("iframe");
        for( var i = 0; i < iframes.length; i++) {
            resizeIFrameToFitContent( iframes[i] );
        }
    } );
    /*
    var frame = document.getElementById("iframe1"); 
          
    // Adjusting the iframe height onload event 
    frame.onload = function() 
    // function execute while load the iframe 
    { 
        alert("hello");
      // set the height of the iframe as  
      // the height of the iframe content 
      frame.style.height =  
      frame.contentWindow.document.body.scrollHeight + 'px'; 
       

     // set the width of the iframe as the  
     // width of the iframe content 
     frame.style.width  =  
      frame.contentWindow.document.body.scrollWidth+'px'; 
          
    } 
    */

    function toggleActualFields() {

        var x = $("#id_0-actual_city");
        var xx =$('#id_0-actual_city').siblings('label[for="id_0-actual_city"]');
        var y = $("#id_0-actual_country");
        var yy =$('#id_0-actual_country').siblings('label[for="id_0-actual_country"]');
        if ($('#id_0-is_actual_country_as_birth_country').is(':checked')) {
           x.attr("hidden", true);
           x.attr("required", true);
           xx.attr("hidden", true);
           y.attr("hidden", true);
           y.attr("required", true);
           yy.attr("hidden", true);

        } else {
            x.attr("hidden", false);
            x.attr("required", false);
            xx.attr("hidden", false);
           y.attr("hidden", false);
           y.attr("required", false);
           yy.attr("hidden", false);
        }
    }

    // Initial check on page load
    toggleActualFields();

    // Toggle visibility on checkbox change
    $('#id_0-is_actual_country_as_birth_country').change(function() {
        toggleActualFields();
    });
});