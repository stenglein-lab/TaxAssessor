

function populateTable(data) {
    TaxAss.tableDiv = '<div class="table-responsive"><table class="table table-hover">';
    TaxAss.tableDiv += '<thead><tr><th>#</th><th>Name</th><th>Count</th><th>taxId</th><th></th></thead>';
    TaxAss.tableDiv += '<tbody>'   
    var i = 1;
    
    var taxaCounts = [];
    jQuery.each(data, function() {
        taxaCounts.push([this.taxId,this.count]);
    });
    taxaCounts.sort(function(a,b) {return b[1] - a[1]});
             
    for (var k=0; k<taxaCounts.length; k++) {
        var taxon = data[taxaCounts[k][0]];
        var buttonHtml = '<div class="btn-group btn-group-xs" role="group">'
        buttonHtml += '<a href="http://www.ncbi.nlm.nih.gov/gquery/?term='+taxon.name+'" target="_blank" type="button" class="btn btn-default">NCBI</a>'
        buttonHtml += '<a href="https://www.google.com/search?q='+taxon.name+'" target="_blank" type="button" class="btn btn-default">Google</a>'
        buttonHtml += '</div>'
        TaxAss.tableDiv += '<tr data-toggle="collapse" data-target="#'+taxon.taxId+'" class="accordion-toggle info">'
        TaxAss.tableDiv += '<td>'+ i++ +'</td>'
        TaxAss.tableDiv += '<th>'+ taxon.name +'</th>'
        TaxAss.tableDiv += '<td>'+ taxon.count +'</td>'
        TaxAss.tableDiv += '<td>'+ taxon.taxId +'</td>'
        TaxAss.tableDiv += '<td>'+ buttonHtml + '</td></tr>'
                

        TaxAss.tableDiv += '<tr><td colspan="5" class="hiddenRow"><div class="accordian-body collapse" id="'+taxon.taxId+'">'
        TaxAss.tableDiv += '<div class="table-responsive hiddenTable"><table class="table" id="taxaTable">';
        TaxAss.tableDiv += '<thead><tr><th>Gene Name</th><th>Coverage</th><th>GeneID</th><th>Present in x Reads</th></thead>';
        TaxAss.tableDiv += '<tbody id="taxaTableBody">' 
        
        var sortable = [];
        for (var gene in taxon.genes) {
            sortable.push([gene,taxon.genes[gene]])
        }
        sortable.sort(function(a,b) {return b[1] - a[1]})
        
        for (var j=0; j<sortable.length; j++) {
            TaxAss.tableDiv += '<tr>'
            TaxAss.tableDiv += '<td><button type="button" class="btn btn-secondary btn-xs getGeneName" value="'+sortable[j][0]+'">Get Name</button></td>'
            TaxAss.tableDiv += '<td><button type="button" class="btn btn-secondary btn-xs getCoverage" data-toggle="modal" data-target=".bs-example-modal-lg" value="'+sortable[j][0]+'">Show Coverage</button></td>'
            TaxAss.tableDiv += '<td>'+sortable[j][0]+"</td>";
            TaxAss.tableDiv += '<td>'+sortable[j][1]+"</td>";
            TaxAss.tableDiv += '</tr>'
        }
        TaxAss.tableDiv += '</tbody></table></div>' 
        TaxAss.tableDiv += '</div></td></tr>'
        
    };
    
     
    TaxAss.tableDiv += '</tbody></table></div>';               

    $('#taxaTableContainer').html(TaxAss.tableDiv);
    
    $('.getGeneName').click(function(e) {
        var cell = $(this);
        var seqId = this.value;
        $('.getGeneName').prop("disabled",true);
              
        var geneName = ""
        var base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
        var extras = '&tool=TaxAssessor&email=jallison_at_colostate.edu'
        
        if (seqId.indexOf('.') === -1) {
            
            var url = base + "efetch.fcgi?db=nucleotide&id="+seqId+"&rettype=docsum&retmode=json" + extras;
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'json',
                success: function(data) {
                    console.log(data);
                    cell.replaceWith(data['result'][seqId]['title']);
                },
                error: function(xhr, status, error) {
                    var err = eval("(" + xhr.responseText + ")");
                    alert(err.Message);
                },
                complete: setTimeout(function() {
                    $('.getGeneName').prop("disabled",false);                  
                },1000)
            });
        }
    })
    
    $('.getCoverage').click(function(e) {
        $('#coverageSvg').empty()
        var seqId = this.value;
        var formData = new FormData($("#get_coverage")[0]);
        formData.append('seqId',this.value);
        $('#coverageModalTitle').html("Coverage Report For: "+this.value)
        $.ajax({
            type: 'POST',
            data: formData,
            dataType: 'json',
            contentType:false,
            processData:false,
            cache:false,
            url: '/getCoverage',
            success: function(coverageData) {
                console.log(coverageData);
                getNcbiCoverageInfo(seqId,coverageData);
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                alert(err.Message);
            },
        });    
      
    })
    
}


             
$(document).ready(function(){
    TaxAss.taxaReport = {}
    TaxAss.taxaReport.json = '../../docs/'+$('#username').attr('value')+
                        '/'+$('#open-file').attr('value')+'_topTenTaxa.json';
  $.ajax({
    type: 'GET',
    dataType: 'json',
    url: TaxAss.taxaReport.json,
    success: function(data) {
        populateTable(data);
    },
    error: function() {
        $('#align-table-data').html('ERROR IN DISPLAYING DATA');
    }
  });
});



function getNcbiCoverageInfo(seqId,coverageData) {

    $('.getGeneName').prop("disabled",true);
          
    var geneName = ""
    var base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
    var extras = '&tool=TaxAssessor&email=jallison_at_colostate.edu'
    
    if (seqId.indexOf('.') === -1) {
        
        var url = base + "efetch.fcgi?db=nucleotide&id="+seqId+"&rettype=docsum&retmode=json" + extras;
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            success: function(ncbiData) {
                console.log(ncbiData);
                createCoverageChart(seqId,coverageData,ncbiData)
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                alert(err.Message);
            },
            complete: setTimeout(function() {
                $('.getGeneName').prop("disabled",false);                  
            },1000)
        });
    }
}

function createCoverageChart(seqId,coverageData,ncbiData) {  

    var ncbiStats = ncbiData['result'][seqId]['statistics']
    console.log(ncbiStats);

    var seqLength = 0
    for (var i=0; i<ncbiStats.length; i++) {
        if (ncbiStats[i].hasOwnProperty('type')) {
            if (ncbiStats[i]['type'] === "Length") {
                seqLength = ncbiStats[i]['count'];
            }
        }
    }
    if (seqLength == 0) {
        seqLength = coverageData.endPos;
    }
    
    console.log(seqLength);

    var xdata = coverageData.positions,
        ydata = coverageData.coverage;
        
    if (xdata[0] != 0) {
        xdata.unshift(0);
        ydata.unshift(0);
    }
    
    if (xdata[xdata.length-1] != seqLength) {
        xdata.push(seqLength);
        ydata.push(0);
    }
        
        
    for (var i=0; i<xdata.length; i++) {
        xdata[i] = +xdata[i];
        ydata[i] = +ydata[i];
    }
        
    //console.log(xdata);

    var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = 1000 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var xScale = d3.scale.linear()
        .domain([0,seqLength])
        .range([0, width]);

    var yScale = d3.scale.linear()
        .domain([0,d3.max(ydata)])
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left");

    var line = function(xdata,ydata) {
        return d3.svg.line()
                 .x(function(d,i) { return xScale(xdata[i]); })
                 .y(function(d,i) { /*console.log(x[i]+","+y[i]);*/ return yScale(ydata[i]); })
                 (Array(xdata.length));
    }

    var svg = d3.select('#coverageSvg')
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
 
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Coverage");

    svg.append("path")
        .attr("class", "line")
        .attr("d", line(xdata,ydata))
        .style("stroke", "steelblue" )
        .attr('fill', 'none');

















    /**
    // size and margins for the chart
    var margin = {top: 25, right: 25, bottom: 25, left: 50},
        width = 1000 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;
        
    //var svg = d3.select('#coverageSvg').append('g');

    // data that you want to plot, I've used separate arrays for x and y values
    var xdata = data.positions,
        ydata = data.coverage;

    // x and y scales, I've used linear here but there are other options
    // the scales translate data values to pixel values for you
    var x = d3.scale.linear()
              .domain([d3.min(xdata), d3.max(xdata)])  // the range of the values to plot
              .range([ 0, width ]);        // the pixel range of the x-axis

    var y = d3.scale.linear()
              .domain([0, d3.max(ydata)])
              .range([ height, 0 ]);

    // the chart object, includes all margins
    var chart = d3.select('#coverageSvg');

    // the main object where the chart and axis will be drawn
    var main = chart.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
    .attr('width', width)
    .attr('height', height)
    .attr('class', 'main')   

    // draw the x axis
    var xAxis = d3.svg.axis()
    .scale(x)
    .orient('bottom');

    main.append('g')
    .attr('transform', 'translate(0,' + height + ')')
    .attr('class', 'main axis date')
    .call(xAxis);

    // draw the y axis
    var yAxis = d3.svg.axis()
    .scale(y)
    .orient('left');

    main.append('g')
    .attr('transform', 'translate(0,0)')
    .attr('class', 'main axis date')
    .call(yAxis);

    // draw the graph object
    var g = main.append("svg:g"); 

    g.selectAll("scatter-dots")
      .data(ydata)  // using the values in the ydata array
      .enter().append("svg:circle")  // create a new circle for each value
          .attr("cy", function (d) { return y(d); } ) // translate y value to a pixel
          .attr("cx", function (d,i) { return x(xdata[i]); } ) // translate x value
          .attr("r", 2) // radius of circle
          .style("opacity", 0.6); // opacity of circle
    
    var lineFunction = d3.svg.line().x(function (d,i) { x(d.position[i]);} )
                                    .y(function (d,i) { y(d.coverage[i]);} );
    g.append("path").attr("d", lineFunction(data));
    **/
}
















