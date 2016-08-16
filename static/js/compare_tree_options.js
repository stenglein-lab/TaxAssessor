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

