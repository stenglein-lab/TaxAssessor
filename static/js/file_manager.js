//
// TAB SWITCHING
//
var currentTab = "open"
$('#manageTabs a[href="#Open"]').click(function (e) {
    currentTab = "open";
    e.preventDefault();
    $(this).tab('show');
    var buttonHtml = "<td><a type='button' class='close glyphicon glyphicon-open openFileButton' style='color:#000050'></td>";
    changeFileButtons(buttonHtml);

    $(".openFileButton").on("click", function(e) {
        var fileName = $(this).parent().parent().children()[1].innerHTML;
        $("#open_file").val(fileName);
        var formData = new FormData($("#open_form")[0]);
        $("#open_form").noValidate = true;
        $.ajax({
            url:"/open",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success:function(resp){
                location.replace("http://stengleinlab101.cvmbs.colostate.edu:2222/sunburst")
            },
            error:function(resp){
                console.log(resp);
            },
            xhr:function(){
                myXhr = $.ajaxSettings.xhr();
                return myXhr;
            }
        });
    })
})

$('#manageTabs a[href!="#Open"]').click(function (e) {
    $('.openFileButton').unbind("click");
})

var selectedSet = null;
$('#manageTabs a[href="#Compare"]').click(function (e) {
    currentTab = "compare";
    e.preventDefault();
    $(this).tab('show');
    $("#compare_sets_button_container").show();
    $("#selectAllFiles").show();

    //Remove the buttons
    changeFileButtons("");

    var container1 = new SetListContainer("set1","panel-info","btn-primary","Set 1","info"),
        container2 = new SetListContainer("set2","panel-success","btn-success","Set 2","success"),
        testType   = new TestType(container1,container2);

    container1.makePanelActive()
    selectedSet = "set1";

    container1.testType = testType;
    container2.testType = testType;

    $('.selectableFiles').click( function() {
        //if it already belongs to a set
        if ($(this).hasClass("info") || $(this).hasClass("success")) {
            $(this).removeClass("info").removeClass("success");
            var fileName = $(this).children()[1].innerHTML,
                fileRow = $(document.getElementById(fileName+"_selected"));

            fileRow.detach()

            container1.updateListStatus();
            container2.updateListStatus();
            container1.resetSetTitle();
            container2.resetSetTitle();
            testType.update();

        //if it does not belong to a set
        } else {
            var container;
            if (selectedSet == "set1") {
                container = container1;
            } else if (selectedSet == "set2"){
                container = container2;
            }
            if (container) {
                container.addItemToList($(this));
                container.updateListStatus();
                container.resetSetTitle();
                testType.update();
            }
        }
    });
    $('.set_clear').click( function() {
        var container;
        if ($(this).attr("id") == "set1_clear") {
            container = container1;
        } else {
            container = container2
        }
        container.removeAllItemsFromList();
        container.resetSetTitle();
        container.updateListStatus();
        testType.update()
    });
    $('.set_save').click( function(e) {
        if ($(this).attr("id") == "set1_save") {
            container1.saveItemsInList();
        } else {
            container2.saveItemsInList();
        }
    });
    $('.set_container').click( function() {
        if ($(this).attr("id") == "set1") {
            selectedSet = "set1";
            container1.makePanelActive();
            container2.makePanelInactive();
        } else {
            selectedSet = "set2";
            container2.makePanelActive();
            container1.makePanelInactive();
        }
    })
    $('#saveSetButton').click( function(e) {
        e.preventDefault();
        var setNameElement = $("#setName"),
            setName = setNameElement.val().trim();

        if (!checkIfSetNameValid(setName,setNameElement)) {return}

        var formData = new FormData($('#save_set_form')[0])
        $.ajax({
            url:"/saveSet",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success:function(resp){
                $('#save_set').modal('hide');
                if (selectedSet == "set1") {
                    container1.title.html(setName);
                } else {
                    container2.title.html(setName);
                }
                $('#setTableBody').append('<tr name='+setName+' class="selectableSets"><td><a type="button" class="close glyphicon glyphicon-open loadSetButton" style="color:#000050" name="loadSet"></a></td><td>'+setName+'</td></tr>');
                $('.selectableSets').unbind();
                $('.loadSetButton').unbind();
                $('.selectableSets').one("mouseenter",populateSetMouseOver);
                $('.selectableSets').mouseout(function () {$(this).popover("hide");});
                $('.loadSetButton').click({container1:container1,container2:container2},
                           loadFileNamesIntoContainer);
            },
            error:function(resp){
                console.log("error");
                console.log(resp);
            }
        });
    });
    $('.selectableSets').one("mouseenter",populateSetMouseOver);
    $('.selectableSets').mouseleave(function () {$(this).popover("hide");});
    $('.loadSetButton').click({container1:container1,container2:container2},
                               loadFileNamesIntoContainer);
    $('#compare_sets_button_container').click({container1:container1,container2:container2},
                                              submitSetsForComparison);
    $("#selectAllFiles").click({container1:container1,container2:container2},
                                selectAllShownFiles);

    function TestType(container1,container2) {
        this.container1 = container1;
        this.container2 = container2;
        this.testContainer = $("#test_type_container");
        this.testText = $("#test_type");
        this.compareButton = $("#compare_sets_submit")

        this.update = function() {
            if (this.container1.nList > 2 && this.container2.nList > 2) {
                this.testContainer.show();
                this.testText.html("t-test between sets")
                this.compareButton.removeClass("disabled")
            } else if ((this.container1.nList > 2 && this.container2.nList == 0) ||
                       (this.container1.nList == 0 && this.container2.nList > 2)) {
                this.testContainer.show();
                this.testText.html("Evaluate z score for each item in set")
                this.compareButton.removeClass("disabled")
            } else if (this.container1.nList <= 2 && this.container2.nList <= 2) {
                this.testContainer.hide();
                this.compareButton.addClass("disabled")
            } else if ((this.container1.nList > 2 && this.container2.nList > 0 && this.container2.nList <= 2) ||
                       (this.container1.nList > 0 && this.container1.nList <= 2 && this.container2.nList > 2)) {
                this.testContainer.hide();
                this.compareButton.addClass("disabled")
            }
        };


    }

    function populateSetMouseOver() {
        var listName = $(this).children()[1].innerHTML;
        $('#getSetName').val(listName);
        var formData = new FormData($('#getSetForm')[0]);
        var button = $(this);
        $.ajax({
            url:"/getSet",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success: function(resp) {
                button.popover({title: listName, content: resp}).popover("show");
                button.mouseenter(function () {button.popover({title: listName, content: resp}).popover("show");})
            },
            error: function(resp) {
                popoverContent = "ERROR";
            }
        });
    }

    function loadFileNamesIntoContainer(event) {
        var container1 = event.data.container1,
            container2 = event.data.container2;
        var listName = $(this).parent().parent().children()[1].innerHTML;
        $('#getSetName').val(listName);
        var formData = new FormData($('#getSetForm')[0]);
        $.ajax({
            url:"/getSet",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success: function(resp) {
                var fileNames = resp.split("\n");
                var container;
                if (selectedSet == "set1") {
                    containerTo   = container1;
                    containerFrom = container2;
                } else {
                    containerTo   = container2;
                    containerFrom = container1;
                }
                containerTo.removeAllItemsFromList();
                containerTo.setSetTitle(listName);
                var startLength = containerFrom.list.children().length
                var missingFileNames = ""
                for (var i=0;i< fileNames.length-1; i++) {
                    containerFrom.removeItemFromList(fileNames[i]);
                    fileListRow = document.getElementById(fileNames[i]);
                    if (fileListRow !== null) {
                        containerTo.addItemToList($(fileListRow));
                    } else {
                        missingFileNames += "<br>"+fileNames[i];
                    }
                }
                if (missingFileNames.length > 0) {
                    console.log('here');
                    containerTo.removeAllItemsFromList();
                    containerTo.resetSetTitle();
                    var errorMessage = "<div class='alert alert-danger alert-block'><strong>-Missing Files-</strong>"+missingFileNames+"</div>"
                    $("#loadErrorFooter").html(errorMessage);
                    $("#loadErrorFooter").show();
                    console.log(errorMessage);
                };
                if (startLength != containerFrom.list.children().length) {containerFrom.resetSetTitle()};
                container1.updateListStatus();
                container2.updateListStatus();

            },
            error: function(resp) {
                popoverContent = "ERROR";
            }
        });
    }

    function SetListContainer(containerId,activePanelClass,activeButtonClass,defaultTitle,selectedRowClass) {
        this.container = $("#"+containerId);
        this.buttons   = $("."+containerId+"_buttons");
        this.list      = $("#"+containerId+"_list");
        this.status    = $("#"+containerId+"_status");
        this.title     = $("#"+containerId+"_title");
        this.nList     = 0;
        this.testType  = null;

        //Panel Toggling
        this.makePanelActive = function() {
            this.container.addClass(activePanelClass).removeClass("panel-default");
            this.buttons.each( function () {
                $(this).addClass(activeButtonClass).removeClass("btn-default");
            });
        }
        this.makePanelInactive = function() {
            this.container.removeClass(activePanelClass).addClass("panel-default");
            this.buttons.each( function () {
                $(this).removeClass(activeButtonClass).addClass("btn-default");
            });
        }
        //Panel Information
        this.updateListStatus = function() {
            this.nList = this.list.children().length;
            if (this.nList == 0) {
                this.status.html("");
            } else {
                this.status.html(this.nList+" files selected");
            }
        }
        this.resetSetTitle = function() {
            this.title.html(defaultTitle);
        }
        this.setSetTitle = function(title) {
            this.title.html(title);
        }
        //List Management
        this.addItemToList = function(fileManagerRow) {
            fileManagerRow.addClass(selectedRowClass);
            var fileName = fileManagerRow.attr("name");
            if ($(document.getElementById(fileName+"_selected")).length == 0) {
                var newPanelRow = $("<a class='list-group-item set-items' id='"+fileName+"_selected'>"+fileName+"</a>");
                this.list.append(newPanelRow);
                var removeRowEvent = (function (event) {
                    event.data.panelRow.remove();
                    event.data.fileManagerRow.removeClass(selectedRowClass);
                    this.updateListStatus();
                    this.resetSetTitle();
                    this.testType.update();
                }).bind(this)
                newPanelRow.click( {panelRow: newPanelRow, fileManagerRow: fileManagerRow}, removeRowEvent );
            }
        }
        this.removeItemFromList = function(fileName) {
            var row = $(document.getElementById(fileName+"_selected"));
            row.remove();
            var fileManagerRow = $(document.getElementById(fileName));
            fileManagerRow.removeClass(selectedRowClass);
        }
        this.removeAllItemsFromList = function() {
            this.list.empty();
            $('#tableBody').children().each( function() {
                    $(this).removeClass(selectedRowClass);
            });
        }
        this.saveItemsInList = function() {
            $('#setFiles').html("");
            this.list.children().each( function() {
                $('#setFiles').html($('#setFiles').html()+this.innerHTML+"\n");
            })
            if ($('#setFiles').is(':empty')) {
                this.status.html("Please select files");
            } else {
                $("#save_set").modal("show");
            }
        }
        //List Output
        this.exportList = function() {
            var setList = new Array();
            this.list.children().each( function() {
                setList.push($(this).html());
            })
            return setList;
        }


    }

    function checkIfSetNameValid(setName,setNameElement) {
        var valid = true;
        if (setName == "") {
            setNameElement.css("background-color","#FFEECC");
            valid = false;
        }
        if (!valid) {return valid}
        $('#setTableBody').children().each( function () {
            if (setName == $(this).children()[1].innerHTML) {
                setNameElement.css("background-color","#FFEECC");
                setNameElement.popover({content: "Set name already exists!",placement:"top"}).popover("show");
                return valid = false;
            }
            return valid;
        });
        return valid;
    }

    function submitSetsForComparison(event) {
        var container1 = event.data.container1,
            container2 = event.data.container2;
        if (container1.list.children().length <= 2 && container2.list.children().length <= 2) {
            $("#compare_sets_button_container").popover({content: "You must select files to compare",placement:"top"}).popover("show");
            setTimeout(function() {
                $("#compare_sets_button_container").popover("destroy");
            }, 2000);
        } else {
            var setLists = {"set1":container1.exportList(),
                            "set2":container2.exportList()}
            $('#set_files_input').val(JSON.stringify(setLists));
            $("#compare_form").submit()
            /*var formData = new FormData($('#compare_form')[0]);
            $("#compare_sets_submit").prop("disabled",true)
            $.ajax({
                url:"/compare",
                type:"POST",
                data:formData,
                contentType:false,
                processData:false,
                cache:false,
                success: function(resp) {
                    console.log(resp.indexOf("Error"));
                    if (resp.indexOf("Error") > -1) {
                        console.log("Error: "+resp);
                    } else {
                        console.log("Success: "+resp);
                    }
                    $("#compare_sets_submit").prop("disabled",false)
                },
                error: function(resp) {
                    console.log("ERROR: "+resp);
                    $("#compare_sets_submit").prop("disabled",false)
                },
                xhr:function(){
                    myXhr = $.ajaxSettings.xhr();
                    return myXhr;
                }
            });*/
        }
    }

    function selectAllShownFiles(event) {
        var container1 = event.data.container1,
            container2 = event.data.container2;
        if (selectedSet == "set1") {
            var container = container1;
        } else if (selectedSet == "set2"){
            var container = container2;
        } else {
            return;
        }
        if (this.checked) {
            $('#tableBody').children().each( function () {
                if ($(this).is(":visible")) {
                    container.addItemToList($(this));
                    container.updateListStatus();
                    testType.update()
                }
            });
        } else {
            $('#tableBody').children().each( function () {
                if ($(this).is(":visible")) {
                    var fileName = $(this).children()[1].innerHTML
                    container.removeItemFromList(fileName);
                    container.updateListStatus();
                    testType.update()
                }
            })
        }
    }
})

$('#manageTabs a[href!="#Compare"]').click(function (e) {
    $('#tableBody').unbind("click");
    $('.selectableFiles').unbind();
    $('.set_clear').unbind();
    $('.set_save').unbind();
    $('.set_container').unbind();
    $('.selectableSets').unbind();
    $('.loadSetButton').unbind();
    $("#compare_sets_button_container").unbind();
    $("#compare_sets_button_container").hide();
    $("#selectAllFiles").hide();
})

$('#manageTabs a[href="#AlignUpload"]').click(function (e) {
    currentTab = "upload";
    e.preventDefault();
    $(this).tab('show');
    changeFileButtons("");
    $('#upload_button').click( function (event) {
        event.preventDefault();
        if (!file_selected) {
            $('#upload_name').val("Please select file");
            return;
        }
        var formData = new FormData($('#upload_form')[0]),
            fileName = $('#upload_name').val(),
            currentBarContainer = $("<div class='progress'></div>"),
            bar = $("<div class='progress-bar' role='progressbar' aria-valuenow='0' aria-valuemin='0' aria-valuemax='100' style='width: 0%;'>0%</div>");
        $.ajax({
            url:"/upload",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            timeout: 1200000,
            success:function(resp){
                resp = JSON.parse(resp);
                for (var fileName in resp) {
                    var status = resp[fileName];
                    if (status.indexOf("SUCCESS") > -1) {
                        addTableRow(fileName)
                    } else {
                        uploadError(fileName,status);
                    }
                }
                var bar = currentBarContainer.children()[0];
                bar.className = "";
                bar.className = "progress-bar-success";
                setTimeout( function () {
                        currentBarContainer.fadeOut();
                    }, 3000);
            },
            error:function(resp){
                console.log("error");
                console.log(resp);
            },
            xhr:function(){
                $('#bar_container').append(currentBarContainer);
                currentBarContainer.append(bar);
                myXhr = $.ajaxSettings.xhr();
                var currentFile = fileName;
                if(myXhr.upload){
                    myXhr.upload.addEventListener('progress',function(evnt){
                        if(evnt.lengthComputable){
                            var ratio = (evnt.loaded / evnt.total) * 100;
                            if (Math.ceil(ratio) == 100) {
                                bar.html(fileName+": "+"Upload Finished, Processing Files");
                                bar.width("100%");
                                myXhr.upload.removeEventListener('progress',arguments.callee);
                            } else {
                                bar.html(fileName+": "+Math.floor(ratio)+"%");
                                bar.width(Math.floor(ratio)+"%");
                            }
                        }
                    },false);
                }
                return myXhr;
            }
        })
    });
    function uploadError(fileName,error) {
        var errorMessage = "<div class='alert alert-danger alert-dismissible'><button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>&times;</span></button><strong>Error Uploading File: "+fileName+"</strong><br>"+error+"</div>";
        $("#uploadErrorMessage").append(errorMessage);
    }
    $('#clear_upload').click( function(event) {
        $('#uploadOptions').fadeOut();
        $('#upload_form')[0].reset();
        $('#upload_button').addClass('disabled');
    });
    $('#fileFormat').change( function(event) {
        if ($('#fileFormat').val() == "Custom") {
            $('#customFileFormatRow').fadeIn();
        } else {
            $('#customFileFormatRow').fadeOut();
        }
    });
    $('#addDelimiter').click( function(event) {
        $('#additionalDelimiters').append('<select class="form-control delimiter-select" ></label><option>Tab</option><option>Space</option><option>Custom</option></select>');
    });
    $('#removeDelimiter').click( function(event) {
        $('#additionalDelimiters select:last-child').remove();
    });

    $('#delimiters').change( function(e) {
        var value = $(this).val();
        if (value === "Custom") {
            $('.customDelimiter').fadeIn();
        } else {
            $('.customDelimiter').fadeOut();
        }
    });

    $('#headerFile').change( function(e) {
        var file = this.files[0];
        var reader = new FileReader();

        reader.onload = function(progressEvent) {
            $('#headerData').val(this.result);
        }

        reader.readAsText(file);
    });
})

$('#manageTabs a[href!="#AlignUpload"]').click(function (e) {
    $('#upload_button').unbind("click");
    $('#clear_upload').unbind("click");
    $('#fileFormat').unbind();
    $('#addDelimiter').unbind();
    $('#removeDelimiter').unbind();
    $('#delimiters').unbind();
})

$('#manageTabs a[href="#Delete"]').click(function (e) {
    currentTab = "delete";
    e.preventDefault();
    $(".deleteReadFileButton").show();
    $(".readPresent").hide();
    $(this).tab('show');
    var buttonHtml = "<td><a type='button' class='close glyphicon glyphicon-remove deleteFileButton' style='color:#990000' name='deleteFile'></td>"
    changeFileButtons(buttonHtml);
    $(".deleteFileButton").click( function(e) {
        e.preventDefault();
        var row = $(this).parent().parent()
        var fileName = row.children()[1].innerHTML;
        $("#delete_file").val(fileName);
        var formData = new FormData($("#delete_form")[0]);
        $("#delete_form").noValidate = true;
        $.ajax({
            rowInfo: row,
            url:"/delete",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success:function(resp){
                row.remove();
            },
            error:function(resp){

            },
            xhr:function(){
                myXhr = $.ajaxSettings.xhr();
                return myXhr;
            }
        });
    })
})

$('#manageTabs a[href!="#Delete"]').click(function (e) {
    $('.readPresent').show();
    $('.deleteReadFileButton').hide();
});

function changeFileButtons(buttonHtml) {
    var rows = $('.selectableFiles');
    for (var i=0;i<rows.length;i++) {
        rows[i].cells[0].innerHTML = buttonHtml;
    }
}

//
// SUBMITING FORMS (OPEN,UPLOAD, & DELETE)
//
$(".openFileButton").click( function(e) {
    var fileName = $(this).parent().parent().children()[1].innerHTML;
    $("#open_file").val(fileName);
    var formData = new FormData($("#open_form")[0]);
    $("#open_form").noValidate = true;
    $.ajax({
        url:"/open",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            location.replace("http://stengleinlab101.cvmbs.colostate.edu:2222/sunburst")
        },
        error:function(resp){
            console.log(resp);
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            return myXhr;
        }
    });
})

//
//  FILE LISTING & SELECTION FUNCTIONS
//
function addTableRow(fileName) {
    var newRow = "<tr name='"+fileName+"' class='selectableFiles' id='"+fileName+"'><td></td><td>"+fileName+"</td><td>None</td><td id=''>None</td></tr>";
    $('#tableBody').append(newRow);
}

var file_selected = false;
$(document).on('change', '.btn-file :file', function() {
    var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        files = input.get(0).files,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
    file_selected = true;
});

$(document).ready( function() {
    $('.btn-file :file').on('fileselect', function(event, numFiles, label) {

        var input = $(this).parents('.input-group').find(':text'),
            log = numFiles > 1 ? numFiles + ' files selected' : label;
            $('#uploadOptions').fadeIn();
            $('#upload_button').removeClass("disabled");
        if( input.length ) {
            input.val(log);
        } else {
            if( log ) alert(log);
        }
    });
});

//Search Bar Functionality
var doneTypingInterval = 500;  //time in ms
//on keyup, start the countdown
$('#fileName_search').keyup(function(){
    var typingTimer = $(this).data('timer');
    clearTimeout(typingTimer);

    typingTimer = setTimeout(doneTyping, doneTypingInterval);

    $(this).data('timer', typingTimer);
});
//on keydown, clear the countdown
$('#fileName_search').keydown(function(){
    clearTimeout($(this).data('timer'));
});
//user is "finished typing," do something
function doneTyping () {
    var searchName = $('#fileName_search').val().toLowerCase();
    $('#tableBody').children().each( function () {
        var fileName = $(this).attr("name").toLowerCase();
        if (fileName.indexOf(searchName) >= 0) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

$('.addReadFileButton').click( uploadReadFile );

function uploadReadFile(e) {
    $("#alignFileName").val('');
    var button = $(this);
    var fileName = $(this).parent().parent().parent().children()[1].innerHTML;
    console.log(fileName);
    $("#alignFileName").val(fileName);
    $('#readFileUpload').trigger('click');
    $('#readFileUpload').change( function(e) {
        var formData = new FormData($("#uploadReadFileForm")[0]);
        $("#uploadReadFileForm").noValidate = true;
        $.ajax({
            url:"/uploadReadFile",
            type:"POST",
            data:formData,
            contentType:false,
            processData:false,
            cache:false,
            success:function(resp){
                console.log('yay!')
                statusHTML = '<div class="readPresent">Present</div><a type="button" class="glyphicon glyphicon-remove deleteReadFileButton" style="color:#990000; display:none;" name="deleteFile"></a>'
                button.parent().html(statusHTML)
                $('.deleteReadFileButton').unbind('click');
                $('.deleteReadFileButton').click( deleteReadFile );
            },
            error:function(resp){
                console.log(resp);
            },
            xhr:function(){
                myXhr = $.ajaxSettings.xhr();
                return myXhr;
            }
        });
    })
}



$('.deleteReadFileButton').click( deleteReadFile );

function deleteReadFile(e) {
    $("#alignFileNameDeleteForm").val('');
    var button = $(this)
    var fileName = button.parent().parent().parent().children()[1].innerHTML;
    console.log(fileName);
    $("#alignFileNameDeleteForm").val(fileName);
    var formData = new FormData($("#deleteReadFileForm")[0]);
    $("#deleteReadFileForm").noValidate = true;
    $.ajax({
        url:"/deleteReadFile",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            buttonHtml = '<button type="button" class="btn btn-secondary btn-xs addReadFileButton">Add</button>'
            button.parent().html(buttonHtml)
            $('.addReadFileButton').unbind('click');
            $('.addReadFileButton').click( uploadReadFile );
        },
        error:function(resp){
            console.log(resp);
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            return myXhr;
        }
    });
}
