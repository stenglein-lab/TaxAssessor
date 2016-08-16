var inspectOffset = 0;
$('#inspectQueryOffset').val(0);
//Functions used for inspecting individual nodes
var nRows
function CreateInspectTable (json_data) {
    $('#inspect-container').show();
    $('#inspected-taxId').html(json_data.name);
    nRows = json_data.status;
    var lowOffset = inspectOffset + 1,
        highOffset = inspectOffset + 1000 < nRows ? inspectOffset+1000 : nRows;
    if (nRows >= 1000) {
        $('#offset_buttons').show();
        $('#inspected-status-small').html("Showing "+lowOffset+"-"+highOffset+" of "+nRows+" alignments");

    } else {
        $('#offset_buttons').hide();
        $('#inspected-status-small').html("Showing "+nRows+" alignments");
    }

    var readData = "";

    //console.log(json_data["reads"]);
    for (var readName in json_data["reads"]) {
        readData += "<li><a class='readListEntry'>"+readName+": "+json_data["reads"][readName].length+" alignment(s)</a>"
        readData += "<ul type='i' style='display:none;''>"
        for (var i=0; i<json_data["reads"][readName].length; i++) {
            readData += "<li><a class='readListEntry'>Alignment "+(i+1)+"</a><ul style='display:none;''>"
            for (var j=0; j<json_data["reads"][readName][i].length; j++) {
                readData += "<li>"
                if (json_data["header"][j]) {
                    readData += "<b>"+json_data["header"][j].replace(/</g, "&lt;").replace(/>/g, "&gt;")+": </b>";
                }
                readData += json_data["reads"][readName][i][j].replace(/</g, "&lt;").replace(/>/g, "&gt;");
                readData += "</li>"
            }
            readData += "</ul></li>"
        }
        readData += "</ul></li>"
    }



    $('#inpectedReadList').html(readData);

    $('.readListEntry').click(function() {
        $($(this).parent().children()[1]).toggle();
    })


}

$('#query_offset_lower').on('click', function () {
    var value = parseInt($('#inspectQueryOffset').val(),10)
    value -= 1000
    if (value < 0) {
        return
    }
    $('#inspectQueryOffset').val(value);
    $('#inspectForm').submit();
    inspectOffset -= 1000
});

$('#query_offset_raise').on('click', function () {
    var value = parseInt($('#inspectQueryOffset').val(),10)
    value += 1000
    if (nRows) {
        if (value > nRows) {
            return
        }
    }
    $('#inspectQueryOffset').val(value);
    $('#inspectForm').submit();
    inspectOffset += 1000
});



$('#inspectForm').on('submit', function(event) {
    event.preventDefault();
    var formData = new FormData($(this)[0]);
    //window.location.hash = "#inspect-container";
    $.ajax({
        url:"/inspect",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            var alignInfo = JSON.parse(resp);
            console.log(alignInfo);
            CreateInspectTable(alignInfo);
            $("#inspect-container").fadeIn();
            window.location.hash = "#inspect-container";
        },
        error:function(resp){
            console.log(resp);
        },
        xhr:function(){
            myXhr = $.ajaxSettings.xhr();
            return myXhr;
        }
    });
    return false;
})

$('#close-inspect').click( function() {
    $('#inspect-container').hide();
    window.location.hash = "#";
});

$("#vis_options").click(function() {
    var link = $("#vis_options").parent(),
        sidebar = $("#vis_options_sidebar"),
        chart = $("#chart");

    if (link.hasClass("active")) {
        link.removeClass("active");
        sidebar.hide();
        chart.removeClass("col-lg-10 col-md-10 col-lg-push-2 col-md-push-2");
        chart.addClass("col-lg-12 col-md-12");
    } else {
        link.addClass("active");
        sidebar.show();
        chart.addClass("col-lg-10 col-md-10 col-lg-push-2 col-md-push-2");
        chart.removeClass("col-lg-12 col-md-12");
    };
});

