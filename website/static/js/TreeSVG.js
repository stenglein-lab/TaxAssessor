TaxAss.tree = {}

TaxAss.tree.viewOptions = {
  "viewType": "tree",
  "circleScaleRadius" : "log",
  "countCutOff" : 1
};

TaxAss.tree.taxTreeJson = "../../docs/"+$('#username').attr("value")+"/"+
  $('#open-file').attr("value")+"_tree.json";

TaxAss.tree.width = 600;
TaxAss.tree.height = 400;
TaxAss.tree.duration = 500;

//general variables
var i = 0;
//tree layout variables
TaxAss.tree.treeRoot;

TaxAss.tree.zoom = d3.behavior.zoom();
TaxAss.tree.zoom.translate([0, 0]);



TaxAss.tree.createTreeSvg = function() {
  return d3.select("#chart")
      .append("div")
      .classed("svg-container",true)
      .append("svg")
      .attr("preserveAspectRatio","xMinYMin meet")
      .attr("viewBox","0 0 "+TaxAss.tree.width+" "+TaxAss.tree.height)
      //.classed("svg-content-responsive",true)
      .attr("id","main-SVG")
      .append("g")
      .call(TaxAss.tree.zoom.scaleExtent([0.3, 4])
            .on("zoom", redraw));
      //.attr("transform","translate(60,200)");

  function redraw() {
    var translation = d3.event.translate,
      newx = translation[0],
      newy = translation[1];
    TaxAss.tree.canvas.attr("transform",
      "translate(" + newx + "," + newy + ")" + " scale(" + d3.event.scale + ")");
  }
}

TaxAss.tree.buildTree = function() {
  TaxAss.tree.canvas.append("rect")
     .attr("class","overlay")
     .attr("stroke","black")
     .attr("stroke-width","1")
     .attr("x",-TaxAss.tree.width*25)
     .attr("y",-TaxAss.tree.height*50)
     .attr("width",TaxAss.tree.width*100)
     .attr("height",TaxAss.tree.height*100);
    
  tree = d3.layout.tree()
          .separation(function(a, b) { return ((a.parent == TaxAss.tree.treeRoot) && (b.parent == TaxAss.tree.treeRoot)) ? 3 : 1; })
          .nodeSize([25,15]);

  d3.json(TaxAss.tree.taxTreeJson, function(error, flare) {
    TaxAss.tree.treeRoot = flare;
    console.log(flare);
    TaxAss.tree.treeRoot.x0 = TaxAss.tree.height/2;
    TaxAss.tree.treeRoot.y0 = TaxAss.tree.width/10;
    TaxAss.tree.treeRoot.children.forEach(collapseToRoot);
    filterCounts(TaxAss.tree.treeRoot);
    updateTree(TaxAss.tree.treeRoot);
  });

  var diagonal = d3.svg.diagonal()
    .projection(function(d) { return [d.y, d.x]; });
  
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

  function updateTree(source) {
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
          updateTree(d);
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
    var nodes = tree.nodes(TaxAss.tree.treeRoot).reverse(),
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
        d.y = ((d.depth * 100)-((d.depth-1)*30))+TaxAss.tree.height/10;
      } else {
        d.y = (d.depth * 70)+TaxAss.tree.width/10;
      }
      d.x = d.x + TaxAss.tree.height/2;
    });
    
    // updateTree the nodes…
    var node = TaxAss.tree.canvas.selectAll("g.node")
      .data(nodes, function(d) {return d.id || (d.id = ++i);});

    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
      .attr("class", "node")
      .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
      .on("click", click);

    nodeEnter.append("circle")
      .attr("r", function(d) {
        if (TaxAss.tree.viewOptions["circleScaleRadius"] == "log") {
          return (4*Math.log10((100*(d.size/TaxAss.tree.treeRoot.size))+1))+1;
        } else if (TaxAss.tree.viewOptions["circleScaleRadius"] == "linear") {
          return (9*(d.size/TaxAss.tree.treeRoot.size)+1);
        }
      })
      .on('contextmenu', d3.contextMenu(rightClickMenu)) // attach menu to element
      .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; })
      .attr('data-original-title', function(d) { return d.name+"<br>Size: "+Math.round(10*d.size)/10; })
      .attr("class","my_node");

    nodeEnter.append("text")
      .attr("x", function(d) { return (4*Math.log10((100*(d.size/TaxAss.tree.treeRoot.size))+1))+2; })
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
      .duration(TaxAss.tree.duration)
      .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

    nodeUpdateTree.select("circle")
      .attr("r", function(d) {
        if (TaxAss.tree.viewOptions["circleScaleRadius"] == "log") {
          return (4*Math.log10((100*(d.size/TaxAss.tree.treeRoot.size))+1))+1;
        } else if (TaxAss.tree.viewOptions["circleScaleRadius"] == "linear") {
          return (9*(d.size/TaxAss.tree.treeRoot.size)+1);
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
      .duration(TaxAss.tree.duration)
      .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
      .remove();

    nodeExit.select("circle")
      .attr("r", 1e-6);

    nodeExit.select("text")
      .style("fill-opacity", 1e-6);

    // updateTree the links…
    var link = TaxAss.tree.canvas.selectAll("path.link")
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
      .duration(TaxAss.tree.duration)
      .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
      .duration(TaxAss.tree.duration)
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
      'html'   : true,
      'delay'  : {'show':100,'hide':100},
    });
    
    $(".my_text").tooltip({
      'container': 'body',
      'placement': 'bottom',
      'html'   : true,
      'delay'  : {'show':100,'hide':100},
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
    updateTree(d); 
  }

  function filterCounts(d) {   
    var filtered = [];
    if (d._filtered) {
      for (var i=d._filtered.length-1; i > -1; --i) {
        if (d._filtered[i].size >= TaxAss.tree.viewOptions["countCutOff"]) {
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
        if (d.children[i].size < TaxAss.tree.viewOptions["countCutOff"]) {
          filtered.push(d.children[i]);
          d.children.splice(i,1);
        }
      } 
      if (d.children.length == 0) {
        d.children = null;
      }
    } else if (d._children) {
      for (var i=d._children.length-1; i > -1; --i) {
        if (d._children[i].size < TaxAss.tree.viewOptions["countCutOff"]) {
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
        .attr("r", function(d) { return (4*Math.log10((100*(d.size/TaxAss.tree.treeRoot.size))+1))+1; });
      TaxAss.tree.viewOptions["circleScaleRadius"] = "log";
    }
    else if (this.value == 'linear') {
      d3.selectAll("circle").transition()
        .duration(750)
        .delay(function(d, i) { return i * 10; })
        .attr("r", function(d) { return (9*(d.size/TaxAss.tree.treeRoot.size)+1); });
      TaxAss.tree.viewOptions["circleScaleRadius"] = "linear";
    }
  });

  $('#set_count_button').click(function() {
    if ($('#set_count_value').val()) {
      TaxAss.tree.viewOptions["countCutOff"] = $('#set_count_value').val();
      filterCounts(TaxAss.tree.treeRoot);
      updateTree(TaxAss.tree.treeRoot);
    }
  });

  $("#set_count_value").keyup(function(event){
    if(event.keyCode == 13){
      if ($('#set_count_value').val()) {
        TaxAss.tree.viewOptions["countCutOff"] = $('#set_count_value').val();
        filterCounts(TaxAss.tree.treeRoot);
        updateTree(TaxAss.tree.treeRoot);
      }
    }
  });

  $('#reset_SVG').click( function() {
    if (TaxAss.tree.viewOptions["viewType"] == "tree") {
      TaxAss.tree.canvas.transition()
          .duration(1000)
          .attr("transform","translate(0,0)scale(1)");
      TaxAss.tree.zoom.scale(1);
      TaxAss.tree.zoom.translate([0, 0]);
      TaxAss.tree.treeRoot.children.forEach(collapseToRoot);
      TaxAss.tree.viewOptions["circleScaleRadius"] = "log";
      $('#circleLogRadius').prop('checked',true);
      updateTree(TaxAss.tree.treeRoot);
    } else if (TaxAss.tree.viewOptions["viewType"] == "block") {
   
    }
  });
}

TaxAss.tree.svg = TaxAss.tree.createTreeSvg();

TaxAss.tree.canvas = TaxAss.tree.svg.append("g")
  .classed("canvas",true);

TaxAss.tree.buildTree();
