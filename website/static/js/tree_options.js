
//Functions used for inspecting individual nodes
function CreateInspectTable (json_data) {
    $('#inspect-container').show();
    $('#inspected-taxId').html(json_data.name);
    $('#inspected-status-small').html(json_data.status);   
    var myTable = "<div class='table-responsive'><table class='table table-striped inspect-table'><thead><tr><th>queryId</th><th>subjectId</th><th>%Ident</th><th>AlignLen</th><th>nMisMatch</th><th>nGapOpen</th><th>qStart</th><th>qEnd</th><th>subStart</th><th>subEnd</th><th>eVal</th><th>bitScore</th></tr></thead><tbody>"
    var data;
    for (var i = 0; i < json_data.info.length; i++) {
        myTable += "<tr>"
        data = json_data.info[i].split(/,?\s+/);
        for (var j = 0; j < data.length; j++) {
            myTable += "<td>"+data[j]+"</td>";
        }
        myTable += "</tr>"
    }
    myTable += "</tbody></table></div>";
    $('#inspect-results').html(myTable);
}

$('#inspectForm').on('submit', function( event) {
    var formData = new FormData($(this)[0]);
    event.preventDefault();
    $.ajax({
        url:"/inspect",
        type:"POST",
        data:formData,
        contentType:false,
        processData:false,
        cache:false,
        success:function(resp){
            var alignInfo = JSON.parse(resp);
            CreateInspectTable(alignInfo);
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
});

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

