var username=$('#username').attr("value"),
    filename=$('#openFile').attr("value");

var reportJson = "../../docs/"+username+"/"+filename+"_report.json";
var reportData

$(document).ready(function(){
    $.ajax({
        type: "GET",
        dataType: "json",
        url: reportJson,
        success: function(data) {
            populateData(data)
        },
        error: function() {
            $('#align_table_data').html("ERROR IN DISPLAYING DATA");
        }
    });
});

function populateData(data) {
    reportData = data;
    
    var taxData = "",
        alignData = "";
    
    alignData += '<tr><td>Number of Reads</td>' + "<td>" + data['nReads'] + "</td></tr>";
    alignData += '<tr><td>Total Alignments</td>' + "<td>" + data['nAligns'] + "</td></tr>";
    alignData += '<tr><td>Total Genes Aligned To</td>' + "<td>" + data['nGis'] + "</td></tr>";
    alignData += '<tr><td>Fewest Alignments for a read</td>' + "<td>" + data['minAligns'] + "</td></tr>";
    alignData += '<tr><td>Most Alignments for a read</td>' + "<td>" + data['maxAligns'] + "</td></tr>";
    alignData += '<tr><td>Average Alignments per read</td>' + "<td>" + data['aveAligns'] + "</td></tr>";    
    
    $('#align_table_data').html(alignData);
    
    createGiBarChart(data['giBins'],data['giBinCounts']);
    
}


function createGiBarChart(bins,values) {
   
    var data = [];

    for (var i = 0; i < bins.length; i++) {
        data.push({key: bins[i], value: values[i]});
    }
    
    var margin = {top: 20, right: 20, bottom: 70, left: 75},
    width = 600 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;

    var x = d3.scale.ordinal().rangeRoundBands([0, width], .05);

    var y = d3.scale.linear().range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickValues(bins);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(10);
        
    Array.max = function( array ){
        return Math.max.apply( Math, array );
    };
    
    if (Array.max(values) >= 10000) {
        yAxis.tickFormat(d3.format("e"));
    }
        
    var svg = d3.select("#gi_chart").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", 
              "translate(" + margin.left + "," + margin.top + ")");

    data.forEach(function(d) {
        d.date = d.key;
        d.value = +d.value;
    });
        
    x.domain(data.map(function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.value; })]);

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", "-.55em")
        .attr("transform", "rotate(-90)" );
        
    d3.select(".x")
        .append("text")
        .attr("transform", "rotate(90)" )
        .attr("y", -width)
        .attr("dy", "-0.5em")
        .attr("x", 0)
        .attr("dx", "-0.5em")
        .text("# GIs");

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("y", 0)
        .attr("dy", "-0.5em")
        .attr("x", 0)
        .attr("dx", "0.5em")
        .style("text-anchor", "end")
        .text("# Reads");

    svg.selectAll("bar")
        .data(data)
        .enter().append("rect")
        .style("fill", "steelblue")
        .attr("x", function(d) { return x(d.date); })
        .attr("width", x.rangeBand())
        .attr("y", function(d) { return y(d.value); })
        .attr("height", function(d) { return height - y(d.value); });
}






