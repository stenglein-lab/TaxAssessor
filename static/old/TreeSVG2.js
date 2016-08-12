//Set default parameters and options
var viewParameters = {
    "width"        : 600,
    "height"       : 400,
    "zoomInLimit"  : 0.3,
    "zoomOutLimit" : 4,
    "duration"     : 500
}; 
var viewOptions = {
    "viewType"          : "tree",
    "circleScaleRadius" : "log",
    "countCutOff"       : 1
};  

//Get file information
var username=$('#username').attr("value"),
    filename=$('#openFile').attr("value");
var jsonFile = "../../docs/"+username+"/"+filename+".json",
    root     = null;

//Function to filter the tree limbs based on the number of "reads" supporting those leaves.
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
};
    
    
    
//Create d3js tree "class"
var TreeView = function() {
    //Declare parameters at initialization
        var self            = this; //for use when a variable gets passed to within d3
        var i;
        var diagonal = d3.svg.diagonal().projection(function(d) { return [d.y, d.x]; })
        this.viewElements   = {
            "zoom"     : d3.behavior.zoom(),
            "svg"      : null,
            "canvas"   : null,
        };
    
    //Function to perform zooming and panning operations  
    this.redraw = function() {
        if (self.viewElements["canvas"] != null) {
            self.viewElements["canvas"].attr("transform",
                "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")");           
        }
    };
        
    //Function to create the view that binds to the #chart DOM element
    this.createCanvas = function() {
        //create container for the canvas
        this.viewElements["svg"] = d3.select("#chart")
            .append("div")
                .classed("svg-container",true)
                .append("svg")
                    .attr("preserveAspectRatio","xMinYMin meet")
                    .attr("viewBox","0 0 "+viewParameters['width']+" "+viewParameters['height'])
                    .attr("id","main-SVG")
                    .classed("svg-content-responsive",true)
                    .append("g")
                        .call(this.viewElements["zoom"].scaleExtent([viewParameters['zoomInLimit'],viewParameters['zoomOutLimit']])
                            .on("zoom", this.redraw))
                        .attr("transform","translate("+viewParameters['width']/10+","+viewParameters['height']/2+")");
        //create canvas for drawing the tree onto so only the canvas is moved instead of each tree element when zooming and panning
        this.viewElements["canvas"] = this.viewElements['svg']
            .append("g")
                .classed("graph_canvas",true)
                .append("rect")
                    .attr("class","overlay")
                    .attr("x",-viewParameters['width']*25)
                    .attr("y",-viewParameters['height']*50)
                    .attr("width",viewParameters['width']*100)
                    .attr("height",viewParameters['height']*100);
    };

    //Function to collapse all nodes down to the children of root
    this.collapseToRoot = function(d) {
        root.children.forEach(function collapseToRoot(d) {
            if (d.children) {
                d._children = d.children;
                d._children.forEach(collapseToRoot);
                d.children = null;
            }
        });
    };

    //Function to toggle expansion of subtree of a given node
    this.expand = function(d){   
        var children = (d.children)?d.children:d._children;
        if (d._children) {        
            d.children = d._children;
            d._children = null;       
        }
        if(children)
          children.forEach(expand);
    };
    
    //Function to toggle collapsing of subtree of a given node
    this.collapse = function(d){   
        var children = (d._children)?d._children:d.children;
        if (d.children) {        
            d._children = d.children;
            d.children = null;       
        }
        if(children)
          children.forEach(collapse);
    };
    
    //Function to initialize the first view of the tree
    this.buildTree = function() {   
        root.x0 = 0;
        root.y0 = 0;
        root.children.forEach(this.collapseToRoot);
        filterCounts(root);
        this.updateTree(root);   
 
    };

    // Toggle children on click.
    this.click = function(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        updateTree(d,viewOptions); 
    }
  
    this.computeNodeRadius = function() {
        var size = 0;
        
        return size;
    };
   
    this.updateTree = function (source) {     
        var rightClickMenu = [
            {
                title: 'Inspect Alignments',
                action: function(elm, d, i) {
                    $('#inspectTaxIdInput').val(d.taxId);
                    $('#inspectTaxNameInput').val(d.name);
                    $('#inspectForm').submit();
                }
            },
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
            },
            {
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
            },  
            {
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
            },   
            {
                title: 'Copy Name',
                action: function(elm, d, i) {
                    window.prompt("Copy to clipboard: Ctrl+C, Enter", d.name);
                }
            },   
            {
                title: 'Copy TaxID',
                action: function(elm, d, i) {
                    window.prompt("Copy to clipboard: Ctrl+C, Enter", d.taxId);
                }
            },          
        ];   
        
        // Compute the new tree layout.
        var nodes = tree.nodes(root).reverse(),
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
                d.y = ((d.depth * 100)-((d.depth-1)*50)); 
            } else {
                d.y = d.depth * 50;
            }
        });
           
        // updateTree the nodes…
        var node = this.viewElements["canvas"].selectAll("g.node")
            .data(nodes, function(d) {return d.id || (d.id = ++i);});

        console.log(this.viewElements);
            
        // Enter any new nodes at the parent's previous position.
        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
            .on("click", this.click);

        nodeEnter.append("circle")
            .attr("r", function(d) {
                if (viewOptions["circleScaleRadius"] == "log") {
                    return (4*Math.log10((100*(d.size/root.size))+1))+1;
                } else if (this.iewOptions["circleScaleRadius"] == "linear") {
                    return (9*(d.size/root.size)+1);
                }
            })
            .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
            .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; })
            .attr('data-original-title', function(d) { //tooltip information
                if (!d.children) {
                    return "Size: "+Math.round(10*d.size)/10; 
                } else {
                    return "Name: "+d.name+"<br>Size: "+Math.round(10*d.size)/10; 
                }
            })
            .attr("class","my_node");

        nodeEnter.append("text")
            .attr("x", function(d) { return d.children || d._children ? 0 : 10; })
            .attr("dy", function(d) { return d.children || d._children ? "-"+((4*Math.log10((100*(d.size/root.size))+1))+2)/6.5+"em" : "0.35em"; })
            .attr("text-anchor", function(d) { return d.children || d._children ? "middle" : "start"; })
            .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
            .text(function(d) { return d.name;})
            .style("fill-opacity", 1e-6);

        // Transition nodes to their new position.
        var nodeUpdateTree = node.transition()
            .duration(viewParameters["duration"])
            .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

        nodeUpdateTree.select("circle")
            .attr("r", function(d) {
                if (viewOptions["circleScaleRadius"] == "log") {
                    return (4*Math.log10((100*(d.size/root.size))+1))+1;
                } else if (viewOptions["circleScaleRadius"] == "linear") {
                    return (9*(d.size/root.size)+1);
                }
            })
            .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; })
            .attr("title",function(d) {return "Size: "+Math.round(10*d.size)/10;})
            .attr('data-original-title', function(d) {
                if (!d.children) {
                    return "Size: "+Math.round(10*d.size)/10; 
                } else {
                    return "Name: "+d.name+"<br>Size: "+Math.round(10*d.size)/10; 
                }
            })
            .attr("class","my_node");

        nodeUpdateTree.select("text")
            .style("fill-opacity", 1)
            .text(function(d) { 
                if (!d.children) {
                    return d.name; 
                } else {
                    return "";
                }
            });
            
        // Transition exiting nodes to the parent's new position.
        var nodeExit = node.exit().transition()
            .duration(viewParameters["duration"])
            .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
            .remove();

        nodeExit.select("circle")
            .attr("r", 1e-6);

        nodeExit.select("text")
            .style("fill-opacity", 1e-6);

        // updateTree the links…
        var link = this.viewElements["canvas"].selectAll("path.link")
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
            .duration(viewParameters["duration"])
            .attr("d", diagonal);

        // Transition exiting nodes to the parent's new position.
        link.exit().transition()
            .duration(viewParameters["duration"])
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
        
        console.log(nodes);

        $(".my_node").tooltip({
            'container': 'body',
            'placement': 'bottom',
            'html'     : true,
            'delay'    : {'show':100,'hide':100},
        });
        
        console.log("here");
    }
        
}

var treeView = new TreeView();
treeView.createCanvas();

tree = d3.layout.tree()
    .separation(function(a, b) { return ((a.parent == root) && (b.parent == root)) ? 3 : 1; })
    .nodeSize([25,15]);

d3.json(jsonFile, function(error,json) {
    root = json;
    treeView.buildTree();
    
});



