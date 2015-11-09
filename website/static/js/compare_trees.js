var currentFile = $('#compareFileNames').val();

var viewOptions = {
    "viewType": "tree",
    "circleScaleRadius" : "linear",
    "countCutOff" : 10
};

var username=$('#username').attr("value"),
    filename=$('#openFile').attr("value");

var width  = 600,
    height = 400,
    duration = 500;

var i = 0;

var tree,
    treeRoot,
    truncated;

var zoom = d3.behavior.zoom();
zoom.translate([0, 0]);

var svg = d3.select("#chart")
            .append("div")
            .classed("svg-container",true)
            .append("svg")
            .attr("preserveAspectRatio","xMinYMin meet")
            .attr("viewBox","0 0 "+width+" "+height)
            .attr("id","main-SVG")
            
var zoomableSvg = svg.append("g")
    .call(zoom.scaleExtent([0.3, 4])
    .on("zoom", redraw));
                      
var canvas = zoomableSvg.append("g")
    .classed("graph_canvas",true);

var diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });

buildTree(canvas);

function redraw() {
    var translation = d3.event.translate,
        newx = translation[0],
        newy = translation[1];
    canvas.attr("transform",
        "translate(" + newx + "," + newy + ")" + " scale(" + d3.event.scale + ")");
}

function buildTree(canvas) {
    canvas.append("rect")
       .attr("class","overlay")
       .attr("stroke","black")
       .attr("stroke-width","1")
       .attr("x",-width*25)
       .attr("y",-height*50)
       .attr("width",width*100)
       .attr("height",height*100);
        
    tree = d3.layout.tree()
                    .separation(function(a, b) { return ((a.parent == treeRoot) && (b.parent == treeRoot)) ? 3 : 1; })
                    .nodeSize([25,15]);

    treeRoot = jsonTree;
    treeRoot.x0 = height/2;
    treeRoot.y0 = width/10;
    treeRoot.children.forEach(collapseToRoot);
    filterCounts(treeRoot);
    updateTree(treeRoot,viewOptions);
}

function collapseToRoot(d) {
    if (d.children) {
        d._children = d.children;
        d._children.forEach(collapseToRoot);
        d.children = null;
    }
}

function expand(d){
    var children = (d.children)?d.children:d._children;
    if (d._children) {        
        d.children = d._children;
        d._children = null;       
    }
    if(children)
      children.forEach(expand);
}

function collapse(d){   
    var children = (d._children)?d._children:d.children;
    if (d.children) {        
        d._children = d.children;
        d.children = null;       
    }
    if(children)
      children.forEach(collapse);
}

function nodeSize(d) {
    var size = Math.abs(d.zscores[currentFile]);
    if (viewOptions["circleScaleRadius"] == "log") {
        return (4*Math.log10((100*(size))+1))+1;
    } else if (viewOptions["circleScaleRadius"] == "linear") {
        return (9*(size/5)+1);
    }
}
function textPos(d) {
    var size = Math.abs(d.zscores[currentFile]);
    if (viewOptions["circleScaleRadius"] == "log") {
        return (4*Math.log10((100*(size))+1))+2;
    } else if (viewOptions["circleScaleRadius"] == "linear") {
        return (9*(size/5)+2);
    }
}
function nodeFillColor(d) {
    var size = d.zscores[currentFile];
    var fill;
    if (size > 0) {
        fill   = d._children ? "lightsteelblue" : "#fff";
    } else if (size < 0) {
        fill   = d._children ? "#FF6666" : "#fff";
    } else if (size == 0) {
        fill   = d._children ? "#AEAEAE" : "#fff";
    }
    return fill;
}

function nodeStrokeColor(d) {
    var size = d.zscores[currentFile];
    var stroke;
    if (size > 0) {
        stroke = "steelblue";
    } else if (size < 0) {
        stroke = "#BE0000";
    } else if (size == 0) {
        stroke = "#0D0D0D";
    }
    return stroke;
}

function updateTree(source,viewOptions) {
    var rightClickMenu = [
        {
            title: "Toggle subtree",
            action: function toggleSubtree(elm, d, i) {
                if (!d._children) {
                    collapse(d);
                } else if (!d.children) {
                    expand(d);
                }
                updateTree(d,viewOptions);
            }
        },{
            title: "Inspect z-scores",
            action: plotBarChart
        },{
            title: 'Google Taxon',
            action: function(elm, d, i) {
                var taxonSearch = d.name.split(" ");
                    taxonSearchUrl = "http://www.google.com/search?q="
                for(var i =0; i < taxonSearch.length; i++){
                    taxonSearchUrl += taxonSearch[i] + "+";
                }
                taxonSearchUrl = taxonSearchUrl.substring(0, taxonSearchUrl.length - 1);
                var win = window.open(taxonSearchUrl, '_blank');
                if(win){
                    //Browser has allowed it to be opened
                    win.focus();
                }else{
                    //Browser has blocked it
                    alert('Please allow popups for this site');
                }
            }
        },{
            title: 'Lookup Taxon on NCBI',
            action: function(elm, d, i) {
                var taxonSearch = d.name.split(" ");
                    taxonSearchUrl = "http://www.ncbi.nlm.nih.gov/gquery/?term="
                for(var i =0; i < taxonSearch.length; i++){
                    taxonSearchUrl += taxonSearch[i] + "+";
                }
                taxonSearchUrl = taxonSearchUrl.substring(0, taxonSearchUrl.length - 1);
                var win = window.open(taxonSearchUrl, '_blank');
                if(win){
                    //Browser has allowed it to be opened
                    win.focus();
                }else{
                    //Broswer has blocked it
                    alert('Please allow popups for this site');
                }
            }
        },{
            title: 'Copy Name',
            action: function(elm, d, i) {
                window.prompt("Copy to clipboard: Ctrl+C, Enter", d.name);
            }
        },{
            title: 'Copy TaxID',
            action: function(elm, d, i) {
                window.prompt("Copy to clipboard: Ctrl+C, Enter", d.taxId);
            }
        },          
    ];

    // Compute the new tree layout.
    var nodes = tree.nodes(treeRoot).reverse(),
        links = tree.links(nodes);
        
    // Normalize for fixed-depth.
    nodes.forEach(function(d) { 
        var rank = d.depth;
        var reduceDepth = false;
        for (var i = 0; i < nodes.length; i++) {
            if (rank == nodes[i].depth && nodes[i].children) {
                reduceDepth = true;
            }
        }
        if (!reduceDepth) {
            d.y = ((d.depth * 100)-((d.depth-1)*30))+height/10;
        } else {
            d.y = (d.depth * 70)+width/10;
        }
        d.x = d.x + height/2;
    });
  
    // updateTree the nodes…
    var node = canvas.selectAll("g.node")
        .data(nodes, function(d) {return d.id || (d.id = ++i);});

    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
        .on("click", click);

    nodeEnter.append("circle")
        .attr("r", nodeSize)
        .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
        .style("fill", nodeFillColor)
        .style("stroke", nodeStrokeColor)
        .attr('data-original-title', function(d) { return d.name+"<br>Size: "+Math.round(10*d.zscores[currentFile])/10; })
        .attr("class","my_node");

    nodeEnter.append("text")
        .attr("x", textPos)
        .attr("dy", function(d) { return "0.3em"; })
        .attr("text-anchor", function(d) { return "start"; })
        .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
        .text(function(d) { return d.name; })
        .style("fill-opacity", 1e-6)
        .attr('data-original-title', function(d) { return "Name: "+d.name })
        .attr("class","my_text")
        .style("cursor","default");
        
    

    // Transition nodes to their new position.
    var nodeUpdateTree = node.transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });


        
    nodeUpdateTree.select("circle")
        .attr("r", nodeSize)
        .style("fill", nodeFillColor)
        .style("stroke", nodeStrokeColor)
        .attr("title",function(d) {return "Size: "+Math.round(10*d.size)/10;})
        .attr('data-original-title', function(d) { 
            return d.name+"<br>Size: "+Math.round(10*d.zscores[currentFile])/10; 
        })
        .attr("class","my_node");

    nodeUpdateTree.select("text")
        .style("fill-opacity", 1)
        .text(function(d) { 
            var name;
            if (!d.children) { return (d.name.length > 18) ? d.name.substring(0,17).trim()+".." : d.name;}
        })
        .attr('data-original-title', function(d) { return d.name })
        .attr("class","my_text")
        .style("cursor","default");
    
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
        .remove();

    nodeExit.select("circle")
        .attr("r", 1e-6);

    nodeExit.select("text")
        .style("fill-opacity", 1e-6);

    // updateTree the links…
    var link = canvas.selectAll("path.link")
        .data(links, function(d) { return d.target.id; });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function(d) {
            var o = {x: source.x0, y: source.y0};
            return diagonal({source: o, target: o});
        });

    // Transition links to their new position.
    link.transition()
        .duration(duration)
        .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(duration)
        .attr("d", function(d) {
            var o = {x: source.x, y: source.y};
            return diagonal({source: o, target: o});
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function(d) {
        d.x0 = d.x;
        d.y0 = d.y;
    });

    $(".my_node").tooltip({
        'container': 'body',
        'placement': 'bottom',
        'html'     : true,
        'delay'    : {'show':100,'hide':100},
    });
    
    $(".my_text").tooltip({
        'container': 'body',
        'placement': 'bottom',
        'html'     : true,
        'delay'    : {'show':100,'hide':100},
    });
}

// Toggle children on click.
function click(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
    } else {
        d.children = d._children;
        d._children = null;
    }
    updateTree(d,viewOptions); 
}

function filterCounts(d) {   
    return
    var filtered = [];
    if (d._filtered) {
        for (var i=d._filtered.length-1; i > -1; --i) {
            if (d._filtered[i].size <= viewOptions["countCutOff"]) {
                if (d.children) {
                    d.children.push(d._filtered[i]);
                } else if (d._children) {
                    d._children.push(d._filtered[i]);
                }
                d._filtered.splice(i,1);
            }
        }
        if (d._filtered.length == 0) {
            d._filtered = null;
        }
    }
    if (d.children) {
        for (var i=d.children.length-1; i > -1; --i) {
            if (d.children[i].size > viewOptions["countCutOff"]) {
                filtered.push(d.children[i]);
                d.children.splice(i,1);
            }
        } 
        if (d.children.length == 0) {
            d.children = null;
        }
    } else if (d._children) {
        for (var i=d._children.length-1; i > -1; --i) {
            if (d._children[i].size > viewOptions["countCutOff"]) {
                filtered.push(d._children[i]);
                d._children.splice(i,1);
            }
        } 
        if (d._children.length == 0) {
            d._children = null;
        }
    }
    if (filtered.length > 0) {
        d._filtered = filtered;
    }
    
    if (d.children) {
        d.children.forEach(filterCounts);
    } else if (d._children) {
        d._children.forEach(filterCounts);
    }
}

$('input[name=circleScaleRadios]:radio').on("change", function() {
    if (this.value == 'log') {
        viewOptions["circleScaleRadius"] = "log";
    }
    else if (this.value == 'linear') {
        viewOptions["circleScaleRadius"] = "linear";
    }
    d3.selectAll("circle").transition()
        .duration(750)
        .delay(function(d, i) { return i * 10; })
        .attr("r", nodeSize);
    d3.selectAll("text").transition()
        .duration(750)
        .delay(function(d, i) { return i * 10; })
        .attr("x", textPos)
});

$('#set_count_button').click(function() {
    if ($('#set_count_value').val()) {
        viewOptions["countCutOff"] = $('#set_count_value').val();
        filterCounts(treeRoot);
        updateTree(treeRoot,viewOptions);
    }
});

$("#set_count_value").keyup(function(event){
    if(event.keyCode == 13){
        if ($('#set_count_value').val()) {
            viewOptions["countCutOff"] = $('#set_count_value').val();
            filterCounts(treeRoot);
            updateTree(treeRoot,viewOptions);
        }
    }
});

$('#reset_SVG').click( function() {
    canvas.transition()
          .duration(1000)
          .attr("transform","translate(0,0)scale(1)");
    zoom.scale(1);
    zoom.translate([0, 0]);
    treeRoot.children.forEach(collapseToRoot);
    viewOptions["circleScaleRadius"] = "linear";
    $('#circleLinearRadius').prop('checked',true);
    updateTree(treeRoot,viewOptions);
});

$('#compareFileNames').change( function() {
    currentFile = $('#compareFileNames').val();
    d3.selectAll("circle").transition()
        .duration(200)
        .delay(function(d, i) { return i * 10; })
        .attr("r", nodeSize)
        .attr('data-original-title', function(d) { 
            return d.name+"<br>Size: "+Math.round(10*d.zscores[currentFile])/10; 
        })
        .style("fill", nodeFillColor)
        .style("stroke", nodeStrokeColor);
    d3.select(".graph_canvas").selectAll("text").transition()
        .duration(100)
        .delay(function(d, i) { return i * 10; })
        .attr("x", textPos);   
})

function countEntries(obj) {
    var count = 0;
    for (var prop in obj) {
        if (obj.hasOwnProperty(prop)) {
            ++count;
        }
    }
}

function plotBarChart(elm, d, i) {
    $(".barGraph").remove()
    
    var data = new Array(),
        names = new Array(),
        values = new Array();
    for (name in d.zscores) {
        names.push(name);
        values.push(d.zscores[name]);
        data.push({"name":name,"value":d.zscores[name]})
    }
    var nSet = countEntries(d.zscores[currentFile]);
    
    var margin = {top:40,right:10,bottom:10,left:width-width/5}    
    var xScale = d3.scale.linear()
        .range([0,width/5]);
    var yScale = d3.scale.ordinal()
        .rangeRoundBands([0,height-margin.top-margin.bottom], .1);
        
    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("top");
    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("right");
    
    var barGroup = svg.append("g")
        .attr("class","barGraph")
        .attr("transform","translate("+(margin.left-margin.right)+","+margin.top+")");
        
    yScale.domain(names);
    
    xScale.domain([-5,5]);
    
    console.log(data);
    
    barGroup.selectAll(".bar")
        .data(data)
      .enter().append("rect")
        .attr("class", function(d) { return d.value < 0 ? "bar negative" : "bar positive"; })
        .attr("x", function(d) { return xScale(Math.min(0, d.value)); })
        .attr("y", function(d) { return yScale(d.name); })
        .attr("width", function(d) { return Math.abs(xScale(d.value) - xScale(0)); })
        .attr("height", yScale.rangeBand());

    var xAxisNodes = barGroup.append("g")
        .attr("class","x axis")
        .attr("transform","translate(0,0)")
        .style({ 'stroke': 'Black', 'fill': 'none', 'stroke-width': '1px'})
        .call(xAxis);
    xAxisNodes.selectAll("text")
        .style({"fill":"black","stroke":"none","font-size":"8px"});
    
    var yAxisNodes = barGroup.append("g")
        .attr("class","y axis")
        .attr("transform","translate("+width/10+",0)")
        .style({ 'stroke': 'Black', 'fill': 'none', 'stroke-width': '1px'})
        .call(yAxis);
    yAxisNodes.selectAll("text").remove();
    yAxisNodes.selectAll(".tick").remove();
}













