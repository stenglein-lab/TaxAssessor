function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$('#upload_form').on('submit', function(){
    var formData = new FormData($(this)[0]); 
    $('#upload_progress').show();
    $('#upload_progress_bar').width("0%");
    $.ajax({
        url:"/upload",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            $('div#status').html(resp);
            $('#upload_progress').hide();
            $('#upload_progress_bar').width("0%");
        },
        error:function(resp){
            $('div#status').html(resp);
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            if(myXhr.upload){
                myXhr.upload.addEventListener('progress',handleProgress,false);
            }
            return myXhr;
        }
    });
    $('div#status').html('File is being uploaded...');
    return false;
});

handleProgress = function(evnt){
    if(evnt.lengthComputable){
        var ratio = (evnt.loaded / evnt.total) * 100;
        $('#upload_progress_bar').width(ratio+"%")
    }

}

var openForm = document.getElementById('open_form'); 
openForm.noValidate = true;
openForm.addEventListener('submit', function(event) { // listen for form submitting
        if (!event.target.checkValidity()) {
            event.preventDefault();
            document.getElementById('openErrorMessage').style.display = 'block';
        }
    }, false);

var deleteForm = document.getElementById('delete_form'); 
deleteForm.noValidate = true;
deleteForm.addEventListener('submit', function(event) { // listen for form submitting
        if (!event.target.checkValidity()) {
            event.preventDefault();
            document.getElementById('deleteErrorMessage').style.display = 'block';
        }
    }, false);

