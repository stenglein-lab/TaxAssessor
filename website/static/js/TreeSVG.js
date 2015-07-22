var viewOptions = {
    "viewType": "tree",
    "circleScaleRadius" : "log",
    "countCutOff" : 1
};

var username=$('#username').attr("value"),
    filename=$('#openFile').attr("value");

var taxTreeJson = "../../docs/"+username+"/"+filename+"_tree.json";

var width  = 600,
    height = 400,
    duration = 500;

//general variables
var i = 0,
    root;

//tree layout variables
var treeRoot,
    truncated;

//block layout variables
var treemap,
    grandparent,
    blockRoot,
    blockNode,
    formatNumber = d3.format(",d"),
    transitioning,
    margin = {top: 20, right: 0, bottom: 0, left: 0};
var treemapHeight = height - margin.top - margin.bottom
var x = d3.scale.linear()
    .domain([0, width])
    .range([0, width]);
var y = d3.scale.linear()
    .domain([0, treemapHeight])
    .range([0, treemapHeight]);


var zoom = d3.behavior.zoom();
zoom.translate([0, 0]);

var svg = createTreeSvg();

var canvas = svg.append("g")
    .classed("graph_canvas",true);

var diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });

buildTree(canvas);

$('#treeOption').on('click', function() {
    viewOptions["viewType"] = "tree"
    $('.svg-container').remove();
    svg = createTreeSvg();
    canvas = svg.append("g")
        .classed("graph_canvas",true);
    buildTree(canvas);
});

$('#blockOption').on('click', function() {
    viewOptions["viewType"] = "block"
    $('.svg-container').remove();
    svg = createBlockSvg();
    canvas = svg.append("g")
        .classed("block_canvas",true)
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        .style("shape-rendering", "crispEdges");
    blockFigure = new buildBlocks(canvas);
});

function createBlockSvg() {
    return d3.select("#chart")
        .append("div")
        .classed("svg-container",true)
        .append("svg")
        .attr("preserveAspectRatio","xMinYMin meet")
        .attr("viewBox","0 0 "+width+" "+height)
        .classed("svg-content-responsive",true)
        .attr("id","main-SVG");

}

function buildBlocks(canvas) {

    blockRoot = jQuery.extend(true,{},root);

    treemap = d3.layout.treemap()
        .children(function(d, depth) { return depth ? null : d._children; })
        .sort(function(a, b) { return a.value - b.value; })
        .ratio(treemapHeight / width * 0.5 * (1 + Math.sqrt(5)))
        .round(false);

    grandparent = canvas.append("g")
        .attr("class", "grandparent");

    grandparent.append("rect")
        .attr("y", -margin.top)
        .attr("width", width*0.9)
        .attr("height", margin.top);
    
    backButton = canvas.append("g")
        .attr("class", "backButton");
        
    backButton.append("rect")
        .attr("y", -margin.top)
        .attr("x", width * 0.9)
        .attr("width", width*0.10)
        .attr("height",margin.top)
        
    backButton.append("text")
        .attr("x", 6 + width * 0.9)
        .attr("y", 6 - margin.top)
        .attr("dy", ".75em")
        .text("Home");

    grandparent.append("text")
        .attr("x", 6)
        .attr("y", 6 - margin.top)
        .attr("dy", ".75em");

    initialize(blockRoot);
    reassignSize(blockRoot);
    accumulate(blockRoot);
    layout(blockRoot);
    display(blockRoot);

    function initialize(blockRoot) {
        blockRoot.x = blockRoot.y = 0;
        blockRoot.dx = width;
        blockRoot.dy = treemapHeight;
        blockRoot.depth = 0;
    }

    function reassignSize(d) {
        d.value = d.size;
        if (d.children) {
            d.children.forEach(reassignSize);
        }
    }

    function accumulate(d) {
        return (d._children = d.children)
            ? d.value = d.children.reduce(function(p, v) { return p + accumulate(v); }, 0)
            : d.value;
    }

    function layout(d) {
        if (d._children) {
            treemap.nodes({_children: d._children});
            d._children.forEach(function(c) {
                c.x = d.x + c.x * d.dx;
                c.y = d.y + c.y * d.dy;
                c.dx *= d.dx;
                c.dy *= d.dy;
                c.parent = d;
                layout(c);
            });
        }
    }

    function display(d) {
        
        grandparent.datum(d.parent)
            .on("click", transition)
            .select("text")
            .text(name(d));

        var g1 = canvas.insert("g", ".grandparent")
            .datum(d)
            .attr("class", "depth");

        var g = g1.selectAll("g")
            .data(d._children)
            .enter().append("g");

        g.filter(function(d) { return d._children; })
            .classed("children", true)
            .on("click", transition);

        g.filter(function(d) { return !d._children; })
            .classed("no_children", true);

        g.selectAll(".child")
            .data(function(d) { return d._children || [d]; })
            .enter().append("rect")
            .attr("class", "child")
            .call(rect);

        g.append("rect")
            .attr("class", "parent")
            .call(rect)
            .append("title")
            .text(function(d) { return d.value; });

        g.append("text")
            .attr("dy", ".75em")
            .text(function(d) { return d.name; })
            .call(text);

        function transition(d) {
            if (transitioning || !d) return;
            transitioning = true;

            var g2 = display(d),
                t1 = g1.transition().duration(750),
                t2 = g2.transition().duration(750);

            // Update the domain only after entering new elements.
            x.domain([d.x, d.x + d.dx]);
            y.domain([d.y, d.y + d.dy]);

            // Enable anti-aliasing during the transition.
            canvas.style("shape-rendering", null);

            // Draw child nodes on top of parent nodes.
            canvas.selectAll(".depth").sort(function(a, b) { return a.depth - b.depth; });

            // Fade-in entering text.
            g2.selectAll("text").style("fill-opacity", 0);

            // Transition to the new view.
            t1.selectAll("text").call(text).style("fill-opacity", 0);
            t2.selectAll("text").call(text).style("fill-opacity", 1);
            t1.selectAll("rect").call(rect);
            t2.selectAll("rect").call(rect);

            // Remove the old node when the transition is finished.
            t1.remove().each("end", function() {
                canvas.style("shape-rendering", "crispEdges");
                transitioning = false;
            });
        }
        return g;
    }

    function text(text) {
        text.attr("x", function(d) { return x(d.x) + 6; })
            .attr("y", function(d) { return y(d.y) + 6; });
    }

    function rect(rect) {
        rect.attr("x", function(d) { return x(d.x); })
            .attr("y", function(d) { return y(d.y); })
            .attr("width", function(d) { return x(d.x + d.dx) - x(d.x); })
            .attr("height", function(d) { return y(d.y + d.dy) - y(d.y); });
    }

    function name(d) {
        return d.parent ? name(d.parent) + "." + d.name : d.name;
    }
}





















function createTreeSvg() {
    return d3.select("#chart")
            .append("div")
            .classed("svg-container",true)
            .append("svg")
            .attr("preserveAspectRatio","xMinYMin meet")
            .attr("viewBox","0 0 "+width+" "+height)
            //.classed("svg-content-responsive",true)
            .attr("id","main-SVG")
            .append("g")
            .call(zoom.scaleExtent([0.3, 4])
                      .on("zoom", redraw));
            //.attr("transform","translate(60,200)");
}

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

    d3.json(taxTreeJson, function(error, flare) {
        treeRoot = jQuery.extend(true,{},flare);  //deep copies of flare
        root = flare;
        treeRoot.x0 = height/2;
        treeRoot.y0 = width/10;
        treeRoot.children.forEach(collapseToRoot);
        filterCounts(treeRoot);
        updateTree(treeRoot,viewOptions);
    });
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

function updateTree(source,viewOptions) {
    var rightClickMenu = [
        {
            title: 'Inspect Alignments',
            action: function(elm, d, i) {
                $('#inspectTaxIdInput').val(d.taxId);
                $('#inspectTaxNameInput').val(d.name);
                $('#inspectForm').submit();
            }
        },{
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
        .attr("r", function(d) {
            if (viewOptions["circleScaleRadius"] == "log") {
                return (4*Math.log10((100*(d.size/treeRoot.size))+1))+1;
            } else if (viewOptions["circleScaleRadius"] == "linear") {
                return (9*(d.size/treeRoot.size)+1);
            }
        })
        .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
        .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; })
        .attr('data-original-title', function(d) { return d.name+"<br>Size: "+Math.round(10*d.size)/10; })
        .attr("class","my_node");

    nodeEnter.append("text")
        .attr("x", function(d) { return (4*Math.log10((100*(d.size/treeRoot.size))+1))+2; })
        .attr("dy", function(d) { return "0.35em"; })
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
        .attr("r", function(d) {
            if (viewOptions["circleScaleRadius"] == "log") {
                return (4*Math.log10((100*(d.size/treeRoot.size))+1))+1;
            } else if (viewOptions["circleScaleRadius"] == "linear") {
                return (9*(d.size/treeRoot.size)+1);
            }
        })
        .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; })
        .attr("title",function(d) {return "Size: "+Math.round(10*d.size)/10;})
        .attr('data-original-title', function(d) { return d.name+"<br>Size: "+Math.round(10*d.size)/10; })
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
        
    // Transition exiting nodes to the parent's new position.
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
    var filtered = [];
    if (d._filtered) {
        for (var i=d._filtered.length-1; i > -1; --i) {
            if (d._filtered[i].size >= viewOptions["countCutOff"]) {
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
            if (d.children[i].size < viewOptions["countCutOff"]) {
                filtered.push(d.children[i]);
                d.children.splice(i,1);
            }
        } 
        if (d.children.length == 0) {
            d.children = null;
        }
    } else if (d._children) {
        for (var i=d._children.length-1; i > -1; --i) {
            if (d._children[i].size < viewOptions["countCutOff"]) {
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
        d3.selectAll("circle").transition()
            .duration(750)
            .delay(function(d, i) { return i * 10; })
            .attr("r", function(d) { return (4*Math.log10((100*(d.size/treeRoot.size))+1))+1; });
        viewOptions["circleScaleRadius"] = "log";
    }
    else if (this.value == 'linear') {
        d3.selectAll("circle").transition()
            .duration(750)
            .delay(function(d, i) { return i * 10; })
            .attr("r", function(d) { return (9*(d.size/treeRoot.size)+1); });
        viewOptions["circleScaleRadius"] = "linear";
    }
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
    if (viewOptions["viewType"] == "tree") {
        canvas.transition()
              .duration(1000)
              .attr("transform","translate(0,0)scale(1)");
        zoom.scale(1);
        zoom.translate([0, 0]);
        treeRoot.children.forEach(collapseToRoot);
        viewOptions["circleScaleRadius"] = "log";
        $('#circleLogRadius').prop('checked',true);
        updateTree(treeRoot,viewOptions);
    } else if (viewOptions["viewType"] == "block") {
 
    }
});



