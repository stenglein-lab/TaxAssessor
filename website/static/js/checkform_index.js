var form = document.getElementById('upload_form'); 
form.noValidate = true;
form.addEventListener('submit', function(event) { // listen for form submitting
        if (!event.target.checkValidity()) {
            event.preventDefault(); // dismiss the default functionality
            document.getElementById('uploadErrorMessage').style.display = 'block';
        }
    }, false);
