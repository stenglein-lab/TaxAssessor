$(document).on('change', '.btn-file :file', function() {
    var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

$(document).ready( function() {
    $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
        
        var input = $(this).parents('.input-group').find(':text'),
            log = numFiles > 1 ? numFiles + ' files selected' : label;
        
        if( input.length ) {
            input.val(log);
        } else {
            if( log ) alert(log);
        }
    });
});

var file_selected = false;
$("input[name='upFile']").change(function() {
    file_selected=true;
});

var newRow = null;

function addManagerOption(fileName) {
    fileName = fileName.replace(/\.[^/.]+$/, "")
    var table = document.getElementById('fileManageTable');
    newRow = table.rows[1].cloneNode(true);
    newRow.id = fileName;
    newRow.removeAttribute("style");
    newRow.cells[0].children[0].value = fileName;
    newRow.cells[1].innerHTML = fileName;
    newRow.cells[3].setAttribute("id","progress-uploading");
    var tableRef = table.getElementsByTagName('tbody')[0];
    tableRef.appendChild(newRow);
}

function removeManagerOption() {
    var table = document.getElementById('fileManageTable');
    var count = table.rows.length;
    table.removeChild(table[count-1]);
}

function deleteFile(formData,fileName) {
    $.ajax({
        url:"/delete",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            $('div#status').html(resp);
            var row = document.getElementById(fileName);
            row.parentNode.removeChild(row)
            showStatusMessage("File Successfully Deleted","managerErrorMessage");
        },
        error:function(resp){
            $('div#status').html(resp);
            showStatusMessage("Error Deleting File<br>Please reload this page","managerErrorMessage");
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            return myXhr;
        }
    });
    $('div#status').html('File is being uploaded...');
    return false;
}

function uploadFile(formData,fileName) {
    $.ajax({
        url:"/upload",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            console.log("success");
            $('#upload_button').prop('disabled', false);
            $('div#status').html(resp);
            console.log(resp);
            if (resp.indexOf("Error") > -1) {
                console.log("Error'd");
                newRow.setAttribute("class","danger");
                newRow.cells[0].children[0].disabled=true;
                newRow.cells[3].innerHTML = "ERROR";
            } else {
                newRow.cells[3].innerHTML = "Ready";
            }
            showStatusMessage(resp,"managerErrorMessage");
        },
        error:function(resp){
            $('#upload_button').prop('disabled', false);
            $('div#status').html(resp);
            showStatusMessage("ERROR UPLOADING FILE","managerErrorMessage");
            newRow.cells[3].innerHTML = "Error";
            removeManagerOption()
        },
        xhr:function(){
            newRow.cells[3].setAttribute("id","progress-processing");
            $('#upload_button').prop('disabled', true);
            myXhr = $.ajaxSettings.xhr();
            if(myXhr.upload){
                myXhr.upload.addEventListener('progress',function(evnt){
                    if(evnt.lengthComputable){
                        var ratio = (evnt.loaded / evnt.total) * 100;
                        if (Math.ceil(ratio) == 100) {
                            newRow.cells[3].innerHTML = "Processing";
                        } else {
                            newRow.cells[3].innerHTML = Math.floor(ratio)+"%";
                        }
                    }
                },false);
            }
            return myXhr;
        }
    });
    $('div#status').html('File is being uploaded...');
    return false;
}

function openFile(formData,fileName) {
    $.ajax({
        url:"/open",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            $('div#status').html(resp);
            location.replace("http://stengleinlab101.cvmbs.colostate.edu:2222/report")
        },
        error:function(resp){
            $('div#status').html(resp);
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            return myXhr;
        }
    });    
}

$(function() { //FILE MANAGER MODAL
    var submitActor = null;
    var $form = $( '#manage_form' );
    var $submitActors = $form.find( 'button[type=submit]' );

    $form.submit( function( event ) {
        event.preventDefault();
        if ( null === submitActor ) {
            submitActor = $submitActors[0];
        }
        //###----DELETE----###
        if (submitActor.name == "delete") {
            if (!$('input[name="fileName"]:checked').val()) {
                showStatusMessage("No file selected","managerErrorMessage");
            } else if ($('input[name="fileName"]:checked').val() == $("#openFile").attr('value')) {
                showStatusMessage("Please close the file before deleting","managerErrorMessage");
            } else if (!confirm("Are you sure you would like to delete the file: "+$('input[name="fileName"]:checked').val()+"?")) {
                //DO NOTHING
            } else {
                var fileName = $('input[name="fileName"]:checked').val();
                var formData = new FormData($(this)[0]);
                deleteFile(formData,fileName);
            }
        //###----OPEN----###
        } else if (submitActor.name == "open") {
            var formData = new FormData($(this)[0]);
            this.noValidate = true;
            if (!$('input[name="fileName"]:checked').val()) {
                showStatusMessage("No file selected","managerErrorMessage");
            } else {
                openFile(formData,fileName);
            }
        //###----UPLOAD----###
        } else if (submitActor.name == "upload") {
            var inputFile = document.getElementById("upload_file");
            if (!file_selected) {
                showStatusMessage("No file selected for upload","managerErrorMessage");
            } else {
                var fileName = $('input[type=file]').val().replace(/C:\\fakepath\\/i, '');
                var formData = new FormData($(this)[0]);
                addManagerOption(fileName)
                uploadFile(formData,fileName);
            }
        }
        return false;
    });

    $submitActors.click( function( event ) {
        submitActor = this;
    });
});

function showStatusMessage(message,targetId) {
    if (document.getElementById("errorMessage")) {
        document.getElementById("errorMessage").remove();
    };
    var p = document.createElement('p');
    p.setAttribute("id","errorMessage");
    p.innerHTML = "<br>"+message;
    document.getElementById(targetId).appendChild(p);
    document.getElementById(targetId).style.display = "block";
}

$("table :radio").change(function() {
    $(".table tr.active").removeClass("active"); //remove previous active class
    $(this).closest("tr").addClass("active"); //add active to radio selected tr
});

