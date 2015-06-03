function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function addOption(name,targetId) {
    name = name.replace(/\.[^/.]+$/, "")
    var selectTag = document.getElementById(targetId);
    var children = selectTag.children;
    var exists = false;
    for (var i=0; i<children.length; i++) {
        if (name == children[i].text) { 
            exists = true;
        };
    };
    if (!exists) {
        var option = document.createElement('option');
        option.innerHTML = name;
        document.getElementById(targetId).appendChild(option);
    };
}

function removeOption(name, targetId) {
    var selectTag = document.getElementById(targetId);
    var children = selectTag.children;
    for (var i=0; i<children.length; i++) {
        if (name == children[i].text) { 
            child = children[i];
			selectTag.removeChild(child);
            break;
        };
    };
    
}

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

$('#upload_form').on('submit', function(event){
    this.noValidate = true;
    if (!event.target.checkValidity()) {
        event.preventDefault();
        showStatusMessage("No file selected","uploadErrorMessage");
    } else {
        var filename = $('input[type=file]').val().replace(/C:\\fakepath\\/i, '');
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
                addOption(filename,"openFileList");
                addOption(filename,"deleteFileList");
                showStatusMessage(resp,"uploadErrorMessage");
            },
            error:function(resp){
                $('div#status').html(resp);
                $('#upload_progress').hide();
                $('#upload_progress_bar').width("0%");
                showStatusMessage("ERROR UPLOADING FILE","uploadErrorMessage");
            },
            xhr:function(){
                myXhr = $.ajaxSettings.xhr();
                if(myXhr.upload){
                    myXhr.upload.addEventListener('progress',handleProgress,false);
                    showStatusMessage("Upload in progress","uploadErrorMessage");
                }
                return myXhr;
            }
        });
        $('div#status').html('File is being uploaded...');
        return false;
    }
});

handleProgress = function(evnt){
    if(evnt.lengthComputable){
        var ratio = (evnt.loaded / evnt.total) * 100;
        $('#upload_progress_bar').width(ratio+"%")
    }

}

$('#open_form').on('submit', function(event) {
    this.noValidate = true;
    if (!event.target.checkValidity()) {
        event.preventDefault();
        showStatusMessage("No file selected","openErrorMessage");
    } else {
    }
});
    
$('#delete_form').on('submit', function(event){
    this.noValidate = true;
    if (!event.target.checkValidity()) {
        event.preventDefault();
        showStatusMessage("No file selected","deleteErrorMessage");
    } else if ($("#deleteFileList").val()[0] == $("#openFile").attr('value')) {
        event.preventDefault();
        showStatusMessage("Please close the file before deleting","deleteErrorMessage");
    } else {
        var filename = $("#deleteFileList").val()[0];
        var formData = new FormData($(this)[0]); 
        $.ajax({
            url:"/delete",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success:function(resp){
                $('div#status').html(resp);
                removeOption(filename,"openFileList");
                removeOption(filename,"deleteFileList");
                showStatusMessage("File Successfully Deleted","deleteErrorMessage");
            },
            error:function(resp){
                $('div#status').html(resp);
                showStatusMessage("Error Deleting File<br>Please reload this page","deleteErrorMessage");
            },
            xhr:function(){
                myXhr = $.ajaxSettings.xhr();
                return myXhr;
            }
        });
        $('div#status').html('File is being uploaded...');
        return false;
    }
});





