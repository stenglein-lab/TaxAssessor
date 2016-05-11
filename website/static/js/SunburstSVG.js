var taxTreeJson = "../../docs/"+$('#username').attr("value")+"/"+
  $('#open-file').attr("value")+"_tree.json";
  
console.log(taxTreeJson);

$(function () {
  $('[data-toggle="popover"]').popover()
})

var width = 1000,
    height = 1000,
    duration = 1000,
    radius = Math.min(width,height)/2,
    maxShowDepth = 1000,
    maxDepth = 0,
    currentDepth = 0,
    root,
    taxNames = [];

var formatNumber = d3.format(",d")

var x = d3.scale.linear()
    .range([0,2*Math.PI]);
var y = d3.scale.sqrt()
    .range([0,radius]);

var color = d3.scale.category20c();

var svg = d3.select("#chart").append("div")
    .classed("svg-container",true)
  .append("svg")
    .classed("sunburst-svg",true)
    .attr("preserveAspectRatio","xMinYMin meet")
    .attr("viewBox","0 0 "+width+" "+height)
  .append("g")
    .attr("transform", "translate(" + width / 2 + "," + (height / 2) + ")");

/*
svg.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("fill", "gray")
    .attr("transform", "translate(" + -width / 2 + "," + (-height / 2) + ")");;
*/     
var partition = d3.layout.partition()
    .sort(function(a,b) {
        return b.size - a.size;
    })
    .value(function(d) { return d.size; })
    .children(function(d) { return d.children });

var arc = d3.svg.arc()
    .startAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x))); })
    .endAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x + d.dx))); })
    .innerRadius(function(d) { return Math.max(0, y(d.y)*scaleArcRadius(d)); })
    .outerRadius(function(d) { return Math.max(0, y(d.y + d.dy)*scaleArcRadius(d)); });
    
d3.json(taxTreeJson, function(error, root) {
    if (error) throw error;
    getNamesForAutocomplete(root);
    $('#filterName').autocomplete({source: taxNames});
    fillInInvisibleChildren(root);
    //console.log(root);
    partition.nodes(root);
    accordianData(root,null);
    startColors(root);
    assignColor(root);
    findMaxDepth(root);
    buildTable(root);


    function setValue(d) {
        d.value = d.size;
        if (d.children) {
            d.children.forEach(setValue);
        }
    }

    var node = root;
    var rightClickMenu = [
      {
        title: 'Inspect Alignments',
        action: function(elm, d, i) {
            console.log(d);
          $('#inspectTaxIdInput').val(d.taxId);
          $('#inspectTaxNameInput').val(d.name);
          $('#inspectForm').submit();
        }
      },{
        title: 'Filter From View',
        action: function(elm,d,i) {
            function addFilterTag(d) {
                d.handFiltered = true;
                if (d.children) {
                    d.children.forEach(addFilterTag)
                }
            }
            addFilterTag(d);
            updateFilter(root);
            filterTransition();
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
    
    //Create group for arcs
    var g1 = svg.datum(root).selectAll("path")
        .data(partition.nodes)
      .enter().append( "g");
    
    //Have separate group for text (so the text will always be on top)
    var g2 = svg.datum(root).selectAll("path")
        .data(partition.nodes)
      .enter().append('g');
      
    var path = g1.append("path")
        .attr("d", arc)
        .attr('id', function(d) { return d.taxId+"_arc"; })
        .style("display",function(d) { if (d.taxId == -9999) { return 'none' }})
        .style("fill", function(d) { return d.color; })
        .each(stash)
        .on("click", click)
        .on('contextmenu', d3.contextMenu(rightClickMenu))
        .attr('data-original-title', function(d) { return d.name+"<br>Size: "+Math.round(10*d.size)/10; })
        .attr("class","my_node")
        .on("mouseover", function(d) {
            var arcColor = this.style.fill;
            arcColor = darkenRGBColor(arcColor);
            this.style.fill = arcColor;
            this.style.stroke = "#000000";
        })
        .on("mouseout", function(d) {
            var arcColor = this.style.fill;
            arcColor = lightenRGBColor(arcColor);
            this.style.fill = arcColor;
            this.style.stroke = "none";
        });
      
    var titles = path.append("title")
        .text(function(d) { return d.name + "\n" + formatNumber(d.size); });
        
    var text = g2.append("text")
        .style("font-size", "13px")
        .attr("class","label")
        .attr("x", function(d) { return d.x; })
         // Rotate around the center of the text, not the bottom left corner
        .attr("text-anchor", SetTextAnchor)
         // First translate to the desired point and set the rotation
        .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")" + "rotate(" + getAngle(d) + ")"; })                       
        .attr("dx", "0") // margin
        .attr("dy", function (d) {
            if (d.children) {
                return "0em";
            } else {
                return ".35em";
            }
        }) // vertical-align
        .text(SetText)
        .attr("pointer-events","none");
    
    //filterByAbundance(root,"rel",0.0001);    
            
    function SetTextAnchor(d) {
        if (d.children && d.depth <= currentDepth + 2) {
            return "middle";
        } else {
            if (arc.centroid(d)[0] >= 0) {
                return "start";
            } else {
                return "end";
            }            
        }
    }  
         
    function SetText(d) {
        if (currentDepth-1 <= d.depth && d.depth <= currentDepth + 2) {
            if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.5) {
                return d.name;
            } 
        } else if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.05){
            if (!d.children) {
                return d.name;
            } else {
                for (var i=0; i<d.children.length; i++) {
                    var child = d.children[i];
                    if (child.taxId == -9999 && child.size > 0.5*d.size) {
                        return d.name;
                    }
                }
            }
        }
        return null;
    }       
                
    function getAngle(d) {
        if (d.children && d.depth <= currentDepth + 2) {
            var thetaDeg = (180 / Math.PI * (arc.startAngle()(d) + arc.endAngle()(d)) / 2 );
            return (thetaDeg > 90 && thetaDeg < 280) ? thetaDeg - 180 : thetaDeg;
        } else {
            var thetaDeg = (180 / Math.PI * (arc.startAngle()(d) + arc.endAngle()(d)) / 2 - 90);
            return (thetaDeg > 90) ? thetaDeg - 180 : thetaDeg;        
        }

    }

    function stash(d) {
        d.x0 = d.x;
        d.dx0 = d.dx;
    }

    function click(d) {
        //console.log(d);
        node = d;
        currentDepth = d.depth;
        var trans = svg.transition()
            .duration(duration)
            .tween("scale", function() {
                var xd = d3.interpolate(x.domain(), [d.x, d.x + d.dx]),
                    yd = d3.interpolate(y.domain(), [d.y, 1]),
                    yr = d3.interpolate(y.range(), [d.y ? 20 : 0, radius]);
                return function(t) { x.domain(xd(t)); y.domain(yd(t)).range(yr(t)); };
            });
            
        trans.selectAll("path")
            .attrTween("d", function(d) { return function() { return arc(d); }; });

        trans.selectAll('.label')
            .attrTween("transform", function(d) { return function () {
                return "translate(" + arc.centroid(d) + ")" + "rotate(" + getAngle(d) + ")";}})
            .attrTween("text-anchor", function(d) { return function () { return SetTextAnchor(d)}})
            .tween("text", function(d) { 
                return function() {
                    if (currentDepth-1 <= d.depth && d.depth <= currentDepth + 2) {
                        if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.5) {
                            this.textContent = d.name;
                        } else {
                            this.textContent = null;
                        }
                    } else if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.05){
                        if (!d.children) {
                            this.textContent = d.name;
                        } else {
                            var nameSet = false;
                            for (var i=0; i<d.children.length; i++) {
                                var child = d.children[i];
                                if (child.taxId == -9999 && child.dx > 0.5*d.dx) {
                                    this.textContent = d.name;
                                    nameSet = true;
                                }
                            }
                            if (!nameSet) {
                                this.textContent =null;
                            }
                        }
                    } else {
                        this.textContent = null;
                    }
                }
            });
        setTimeout(function() {updateTable(tableRoot,getDisplayedTaxIds(d));},duration)
    }

    function updateFilter(d) {
        if (d.abundanceFilter || d.handFiltered || d.nameFiltered || d.aveScoreFilter) {
            d.hidden = true;
        } else {
            d.hidden = false;
        }
        if (d.children) {
            d.children.forEach(updateFilter)
        }
    }
    
    // When switching data: interpolate the arcs in data space.
    function arcTweenData(a, i) {
        var oi = d3.interpolate({x: a.x0, dx: a.dx0}, a);
        function tween(t) {
            var b = oi(t);
            a.x0 = b.x;
            a.dx0 = b.dx;
            return arc(b);
        }
        if (i == 0) {
        // If we are on the first arc, adjust the x domain to match the root node
        // at the current zoom level. (We only need to do this once.)
            var xd = d3.interpolate(x.domain(), [node.x, node.x + node.dx]);
            return function(t) {
                x.domain(xd(t));
                return tween(t);
            };
        } else {
            return tween;
        }
    }

    function arcTweenText(a, i) {
        var oi = d3.interpolate({x: a.x0, dx: a.dx0}, a);
        function tween(t) {
            var b = oi(t);
            a.x0 = b.x;
            a.dx0 = b.dx;
            return "translate(" + arc.centroid(b) + ")" + "rotate(" + getAngle(b) + ")";
        }
        if (i == 0) {
        // If we are on the first arc, adjust the x domain to match the root node
        // at the current zoom level. (We only need to do this once.)
            var xd = d3.interpolate(x.domain(), [node.x, node.x + node.dx]);
            return function(t) {
                x.domain(xd(t));
                return tween(t);
            };
        } else {
            return tween;
        }
    }
    
    function filterTransition() {
    
        var value = function(d) {
            if (d.hidden) {
                return 0;
            } else {
                return d.size;
            }
        }
                
        path.data(partition.value(value).nodes)

        var trans = svg.transition()
            .duration(duration)
            
        trans.selectAll("path")
            .attrTween("d", arcTweenData)            
            
        trans.selectAll('.label')
            .attrTween("transform", arcTweenText)
            .attrTween("text-anchor", function(d) { return function () { return SetTextAnchor(d)}})
            .tween("text", function(d) { 
                return function() {
                    if (currentDepth-1 <= d.depth && d.depth <= currentDepth + 2) {
                        if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.5) {
                            this.textContent = d.name;
                        } else {
                            this.textContent = null;
                        }
                    } else if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.05){
                        if (!d.children) {
                            this.textContent = d.name;
                        } else {
                            var nameSet = false;
                            for (var i=0; i<d.children.length; i++) {
                                var child = d.children[i];
                                if (child.taxId == -9999 && child.dx > 0.5*d.dx) {
                                    this.textContent = d.name;
                                    nameSet = true;
                                }
                            }
                            if (!nameSet) {
                                this.textContent =null;
                            }
                        }
                    } else {
                        this.textContent = null;
                    }
                }
            });
        setTimeout(function() {updateTable(tableRoot,getDisplayedTaxIds(node));},duration);
    }

    function filterByAbundance(d,type,threshold) {
        var check = type === "count" ? d.size : d.size/root.size;
        if (check < threshold && d.taxId != -9999) {
            d.abundanceFilter = true;
        } else {
            d.abundanceFilter = false;
        }
        if (d.children) {
            for (var i=0; i<d.children.length; i++) {
                filterByAbundance(d.children[i],type,threshold);
                if (d.children[i].taxId == -9999 && d.abundanceFilter) {
                    d.children[i].abundanceFilter = true;
                }
            }
        }
        
    }
    
    function filterByName(d,isInclusive,name) {
        function showChildren(d) {
            d.nameFiltered = false;
            if (d.children) {
                d.children.forEach(showChildren);
            }
        }
        function showParents(d) {
            d.nameFiltered = false;
            if (d.parent) {
                showParents(d.parent);
            }
        }
        function hideChildren(d) {
            d.nameFiltered = true;
            if (d.children) {
                d.children.forEach(hideChildren);
            }
        }
        
        if (name == d.name || name == d.taxId) {
            if (isInclusive) {
                showChildren(d);
                showParents(d);
            } else {
                hideChildren(d);
            }
        }
        
        //Fill in the remaining nodes
        if (d.nameFiltered == null) {
            if (isInclusive) {
                d.nameFiltered = true;
            } else {
                d.nameFiltered = false;
            }
          
        }
        
        if (d.children) {
            for (var i=0; i<d.children.length; i++) {
                filterByName(d.children[i],isInclusive,name);
            }
        }
    }
    
    function filterByAverageScore(d,cutoff,removeHigher) {
        var checkVal = (removeHigher ? d.score : -d.score),
            cutoff = (removeHigher ? cutoff : -cutoff);
        if (checkVal > cutoff) {
            d.aveScoreFilter = true;
        } else {
            d.aveScoreFilter = false;
        }
        if (d.children) {
            for (var i=0; i<d.children.length; i++) {
                filterByAverageScore(d.children[i],cutoff,removeHigher);
            }
        }
      
    }
    
    function fillInInvisibleChildren(d) {
        if (d.children) {
            var totalSize = 0;
            d.children.forEach( function(d) {
                totalSize += d.size;
            })
            if (totalSize < d.size) {
                d.children.push({'name':'','size':d.size-totalSize,'taxId':-9999,'score':d.score})
            }
            d.children.forEach(fillInInvisibleChildren);
        }
    }
    
    $('#backToRoot').click(function() {
        click(root);
    });
    
    $('#removeFilters').click(function(e) {
        $('#filterName').val('');
        $('#filterByFile').val('');
        $('#abundanceAmount').val('0');
        function removeHiddenTags(d) {
            d.abundanceFilter = null;
            d.handFiltered = null;
            d.nameFiltered = null;
            d.aveScoreFilter = null;
            if (d.children) {
                d.children.forEach(removeHiddenTags);
            }
        }
        removeHiddenTags(root);
        updateFilter(root);
        filterTransition();
    });
    
    $('#filterByAbundance').submit(function(e) {
        e.preventDefault();
        
        var threshold = $('#abundanceAmount').val(),
            type = $('.abundanceRadio:checked').val();
            
        threshold = type === "count" ? threshold: threshold/100;
        
        console.log(threshold+","+type);
        filterByAbundance(root,type,threshold);
        updateFilter(root);
        filterTransition();
    });
    
    $('#filterByName').submit(function(e) {
        e.preventDefault();
        var name = $('#filterName').val(),
            type = $('.filterNameRadio:checked').val();

        var isInclusive = false;
        if (type == "inclusive") {
            isInclusive = true;
        }
        filterByName(root,isInclusive,name);
        updateFilter(root);
        filterTransition();
    });
    
    $('#filterByFile').change( function(e) {
        var file = this.files[0];
        var reader = new FileReader();
        
        reader.onload = function(e) {
            var a = reader.result.replace(/\r/g, '\n');
            var b = a.split('\n');
            for (var i=0;i<b.length;i++) {
                var c = b[i].split(',');
                console.log(c);
                if (c.length == 2) {
                    var isInclusive = (c[1] == 'include' ? true : false);
                    filterByName(root,isInclusive,c[0]);
                }
            }
            updateFilter(root);
            filterTransition();
        }
        
        reader.readAsText(file);
    });
    
    $('#filterByAveScore').submit( function(e) {
        e.preventDefault();
        var value = $('#filterAveScore').val(),
            type = $('.filterAveScoreRadio:checked').val();

        var removeHigher = false;
        if (type == "removeHigher") {
            removeHigher = true;
        }
        filterByAverageScore(root,value,removeHigher);
        updateFilter(root);
        filterTransition();
    });
    
    
    $(".my_node").tooltip({
        'container': 'body',
        'placement': 'left',
        'html'   : true,
        'delay'  : {'show':100,'hide':100},
    });
    
});
    
function getNamesForAutocomplete(d) {
    taxNames.push(d.name);
    if (d.children) {
        d.children.forEach(getNamesForAutocomplete)
    }
}


function getDisplayedTaxIds (d) {
    var taxIds = [];
    getTaxIdsFromTree(d);
    return taxIds;
    function getTaxIdsFromTree(d) {
        if (!d.hidden) {
            taxIds.push(d.taxId);
        }
        if (d.children) {
            d.children.forEach( function(child) {
                getTaxIdsFromTree(child);
            });
        }
    }
}

function findMaxDepth(d) {
    if (d.depth > maxDepth) {
        maxDepth = d.depth;
    }
    if (d.children) {
        d.children.forEach(findMaxDepth);
    }
}

function startColors(d) {
    var colors = ["51,204,51",
                  "0,102,255",
                  "255,80,80",
                  "153,153,102",
                  "102,0,255"];
    d.color = "rgb(100,100,100)";
    for (var i=0; i < d.children.length; i++) {
        d.children[i].color = "rgb("+colors[i]+")";
    }
}

function assignColor(d) {
    if (!d.color) {
        //console.log(d);
        var colors = d.parent.color.substring(4,d.parent.color.length-1);
        colors = colors.split(",");
        for (var i=0; i < colors.length; i++) {
            colors[i] = parseInt(colors[i]);
            if (Math.random() < 0.5) {
                if (colors[i] <= 240) {
                    colors[i] += 15;
                }
            } else {
                if (colors[i] >= 15) {
                    colors[i] -= 15;
                }
            }
        }
        var newColors = "rgb("+colors[0]+","+colors[1]+","+colors[2]+")";
        d.color = newColors
    }
    if (d.children) {
        d.children.forEach(assignColor);
    }
}

function scaleArcRadius(d) {
    if (d.depth > maxShowDepth+currentDepth) {
        return 0
    } else {
        return 0.8
    }
}

d3.select(self.frameElement).style("height", height + "px");

function accordianData (d,startParent) {
    if (startParent !== null)  {
        if (!d.children) {
            if ((d.depth - startParent.depth) > 3) {
                startParent.children[0]._accordian = startParent.children[0].children
                startParent.children[0].children = [d]
                startParent.children[0].name = startParent.children[0].name + "..." + d.parent.name;
                d.parent = startParent.children[0]
            }
        } else if (d.children.length == 1) {
            accordianData(d.children[0],startParent);
        } else if (d.children.length > 1) {
            for (var i=0; i < d.children.length; i++) {
                accordianData(d.children[i],null)
            }
            if ((d.depth - startParent.depth) > 3) {
                startParent.children[0]._accordian = startParent.children[0].children
                startParent.children[0].children = [d]
                startParent.children[0].name = startParent.children[0].name + "..." + d.parent.name;
                d.parent = startParent.children[0]
            }
        }
    } else if (startParent == null && d.children) {
        if (d.children.length == 1 ) {
            accordianData(d.children[0],d)
        } else { 
            for (var i=0; i < d.children.length; i++) {
                accordianData(d.children[i],null)
            }
        }    
    }
}

/*
!!!!!BUILD TAXA TABLE!!!!
*/

var margin = {top: 30, right: 20, bottom: 30, left: 20},
    tableWidth = 500 - margin.left - margin.right,
    tableHeight = 1000,
    barHeight = 40,
    barWidth = tableWidth * 1;

var i = 0,
    tableRoot;

var tableSvg = d3.select("#taxaTable").append("div")
    .classed("svg-container",true)
  .append("svg")
    .classed("table-svg",true)
    .attr("preserveAspectRatio","xMinYMin meet")
    .attr("viewBox","0 0 "+tableWidth+" "+tableHeight)
    
var tableCanvas = tableSvg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


/*tableSvg.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("fill", "gray")*/

var taxaReport = '../../docs/'+$('#username').attr('value')+'/'+
                $('#open-file').attr('value')+'_topTenTaxa1.json';

var tableDuration = 1000;

function buildTable(root) {
    d3.json(taxaReport, function(error, flare) {
        if (error) throw error;
        tableRoot = flare;
        tableRoot.sort(function(a,b) {return b['count'] - a['count']})
        updateTable(tableRoot,getDisplayedTaxIds(root));
    });
}

function darkenRGBColor(color) {
    var f = color.split("(");
    f = f[1].split(")");
    f = f[0].split(",");
    f[0] = Math.floor(f[0]*0.5);
    f[1] = Math.floor(f[1]*0.5);
    f[2] = Math.floor(f[2]*0.5);
    return "rgb("+f[0]+","+f[1]+","+f[2]+")";
}

function lightenRGBColor(color) {
    var f = color.split("(");
    f = f[1].split(")");
    f = f[0].split(",");
    f[0] = Math.floor(f[0]*2);
    f[1] = Math.floor(f[1]*2);
    f[2] = Math.floor(f[2]*2);
    return "rgb("+f[0]+","+f[1]+","+f[2]+")";
}  

function updateTable(source,taxaList) {
    var n = source.length;
    if (typeof(taxaList)==='undefined') taxaList = [];
    function color(d) {
        return "#3182bd" ;//: d.genes ? "#c6dbef" : "#fd8d3c";
    }
    
    function opacity(d) {
        return d.display ? 1:1e-6;
    }

    function computeBarWidth(d) {
        return ((d.count/maxCount) * barWidth)+(barWidth*0.02);
    }
    
  
    
    
    
    var maxCount = 0;
    
    if (taxaList.length > 0) {
        maxCount = 0
        source.forEach( function(d) {
            if ($.inArray(d.taxId,taxaList) != -1) {
                if (d.count > maxCount) {
                    maxCount = d.count;
                }
                d.display = true;
            } else {
                d.display = false;
            }
          
        });
    } else {
        source.forEach( function(d) {
            if (d.count > maxCount) {
                maxCount = d.count;
            }
            d.display = true;
        });
    }
    
    var x0 = 0,
        y0 = 0,
        padding = 1,
        shownGenes = [];
        
    //compute new positions
    source.forEach( function(d) {
        if (d.display == true) {
            d.x = x0;
            d.y = y0;
            y0 += barHeight+padding;
        } else {
            d.x = -barWidth*2;
            d.y = y0;
        }
    });

    var tableHeight = y0 + margin.top + margin.bottom;
    
    tableSvg.transition()
        .duration(duration)
        .attr("viewBox","0 0 "+tableWidth+" "+tableHeight)

    d3.select(self.frameElement).transition()
        .duration(duration)
        .style("height", tableHeight + "px");

    var taxa = tableSvg.selectAll(".taxon")
        .data(source);
                
    var taxaEnter = taxa.enter()
        .append("g")
        .classed("taxon",true)
        .attr("transform",function(d) {return "translate(" + d.x + "," + d.y + ")"})
        .style("opacity",1)
        .on("click", function(d) {clickTable(d);})
        .on("mouseover", function(d) {
            d3.select(this).select("rect").style("fill","#999999");
            var arcColor = document.getElementById(d.taxId+'_arc').style.fill;
            arcColor = darkenRGBColor(arcColor);
            document.getElementById(d.taxId+'_arc').style.fill = arcColor;
            document.getElementById(d.taxId+'_arc').style.stroke = "#000000" 
        })
        .on("mouseout", function(d) {
            d3.select(this).select("rect").style("fill",color);
            var arcColor = document.getElementById(d.taxId+'_arc').style.fill;
            arcColor = lightenRGBColor(arcColor);
            document.getElementById(d.taxId+'_arc').style.fill = arcColor;
                        document.getElementById(d.taxId+'_arc').style.stroke = "none" 
        });
        
    var taxaRect = taxaEnter.append("rect")
        .classed("taxonRect",true)
        .attr("height", barHeight)
        .attr("width", 0)
        .style("fill", color);
        
    var taxaText = taxaEnter.append("text")
        .attr("dy", 25)
        .attr("dx", 5.5)
        .style("font-size", "14px")
        .text(function(d) { 
            if(d.name.length > 70) {
                return d.name.substring(0,67)+"...";
            } else {
                return d.name;
            }
        })
        .style("cursor","default")
      

    // Transition nodes to their new position.
    //taxaEnter.transition()
        //.duration(tableDuration)
        //.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
        //.style("opacity", opacity);

    taxa.transition()
        .delay( function(d,i) {return 500})
        .duration(500)
        .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
        //.style("opacity", opacity)
        .select("rect")
        .style("fill", color)
        .attr("width", computeBarWidth);

}

function clickTable(d,startPos) {
    if (typeof(startPos)==='undefined') startPos = 0;
    $('#geneTabs li:eq(0) a').tab('show');
    $('#coverageSvg').empty()
    $('#coverageTitle').html("No gene selected");
    $('.getGeneName').unbind('click');
    $('.getCoverage').unbind('click');
    $('#forwardGenes').unbind('click');
    $('#reverseGenes').unbind('click');
    var tableDiv = "",
        passData = d;
        offset = 20;
    $('.navigateGenes').addClass("disabled")
    setTimeout(function() {$('.navigateGenes').removeClass("disabled");},500)
    $('#forwardGenes').on('click', function(passData) {clickTable(d,startPos+offset);});
    $('#reverseGenes').on('click', function(passData) {clickTable(d,startPos-offset);});
    
    var allSeqIds = []
    
    d.genes.sort(function(a,b) {return b['count'] - a['count']})
    
    d.genes.forEach( function(gene) {
        allSeqIds.push(gene.geneId)
    });
    
    if (d.genes.length < startPos+offset) {
        var endPos = d.genes.length;
        $('#forwardGenes').prop("disabled",true);
    } else {
        var endPos = startPos+offset;
        $('#forwardGenes').prop("disabled",false);
    }
    
    if (startPos==0) {
        $('#reverseGenes').prop("disabled",true);
    } else {
        $('#reverseGenes').prop("disabled",false);
    }
    
    for (var j=startPos; j<endPos; j++) {
        tableDiv += '<tr>';
        tableDiv += '<td>'+(j+1)+'</td>';
        tableDiv += '<td class="geneName" id="'+d.genes[j]['geneId']+'">Loading...</td>';
        tableDiv += '<td><button type="button" class="btn btn-secondary btn-xs disabled getCoverage" value="'+d.genes[j]['geneId']+'" id="'+d.genes[j]['geneId']+'_button">Show Coverage</button></td>';
        tableDiv += '<td>'+d.genes[j]['geneId']+"</td>";
        tableDiv += '<td>'+d.genes[j]['count']+"</td>";
        tableDiv += '</tr>';
    }
    
    getAllGeneNames(allSeqIds.slice(startPos,endPos));
    
    
    $('#geneTableBody').html(tableDiv);
    $('#taxonModalTitle').html(d.name)
    $('#taxonModal').modal('show');
    
    
    $('.getCoverage').click(function(e) {
        console.log(d);
        $('#coverageSvg').empty()
        var geneInfo = {}
        geneInfo['seqId'] = this.value;
        geneInfo['name'] = $('#'+geneInfo['seqId']).html()
        geneInfo['seqLen'] = $(this).attr('length');
        var formData = new FormData($("#get_coverage")[0]);
        formData.append('seqId',this.value);
        formData.append('taxId',d.taxId);
        $.ajax({
            type: 'POST',
            data: formData,
            dataType: 'json',
            contentType:false,
            processData:false,
            cache:false,
            url: '/getCoverage',
            success: function(coverageData) {
                createCoverageChart(geneInfo,coverageData);
            },
            error: function(xhr, status, error) {
                var err = eval("(" + xhr.responseText + ")");
                alert(err.Message);
            },
        });    
    }) 
}

function getAllGeneNames(allSeqIds) {
    var base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
    var extras = '&tool=TaxAssessor&email=jallison_at_colostate.edu'
    var url = base + "efetch.fcgi?db=nucleotide&id="+allSeqIds+"&rettype=docsum&retmode=json" + extras;
    $.ajax({
        type: 'GET',
        url: url,
        dataType: 'json',
        success: function(data) {
            console.log(data);
            data["result"]["uids"].forEach( function(d) {
                var cell = $('#'+d);
                $('#'+d).html(data["result"][d]["title"]);
                $('#'+d+"_button").attr("length",data["result"][d]["slen"]);
                $('#'+d+"_button").removeClass('disabled');
            });
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
            console.log(err);
        },
        complete: removeUnknownNames
    });
    function removeUnknownNames() {
        $('.geneName').each( function(d) {
            if ($(this).html() == "Loading...") {
                $(this).html("Name unknown");
            }
        });
    }
}


/*function getNcbiCoverageInfo(seqId,coverageData) {
          
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
}*/

function createCoverageChart(geneInfo,coverageData) {  

    $('#coverageTitle').html("Coverage Report For: "+geneInfo['name'])
    var seqLength = geneInfo['seqLen'];
    if (!seqLength) {
        seqLength = coverageData.endPos;
    }
    var data = coverageData.coverageData,
        readData = coverageData.readData;

    data.forEach(function(d) {
        d.position = +d.position;
        d.coverage = +d.coverage;
    });
    
    readData.forEach(function(d) {
        d.startPos = +d.startPos;
        d.endPos = +d.endPos;
        d.depth = +d.depth;
        d.score = +d.score;
    });
        
    if (data[0].position != 0) {
        data.unshift({"coverage":0,"position":0});
    }
    
    if (data[data.length-1] != seqLength) {
        data.push({"coverage":0,"position":seqLength});
    }
    
    var margin = {top: 20, right: 60, bottom: 30, left: 20},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom,
        levelOfDetail = width*0.1,
        yExtentOffset = 0;

    var x = d3.scale.linear()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);
        
    var colorScale = d3.scale.log()
        .base(10)
        .range(['#0000ff','#ff0000']);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickSize(-height, 0)
        .tickPadding(6);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("right")
        .tickSize(-width)
        .tickPadding(6);

    var area = d3.svg.area()
        .interpolate("step-after")
        .x(function(d) { return x(d.position); })
        .y0(y(0))
        .y1(function(d) { return y(d.coverage); });

    var line = d3.svg.line()
        .interpolate("step-after")
        .x(function(d) { return x(d.position); })
        .y(function(d) { return y(d.coverage); });

    var svg = d3.select('#coverageSvg').append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var zoom = d3.behavior.zoom()
        .on("zoom", draw);

    var gradient = svg.append("defs").append("linearGradient")
        .attr("id", "gradient")
        .attr("x2", "0%")
        .attr("y2", "100%");

    gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", "#fff")
        .attr("stop-opacity", .5);

    gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", "#999")
        .attr("stop-opacity", 1);

    svg.append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("x", x(0))
        .attr("y", y(1))
        .attr("width", x(1) - x(0))
        .attr("height", y(0) - y(1));

    svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + width + ",0)");

    svg.append("path")
        .attr("class", "area")
        .attr("clip-path", "url(#clip)")
        .style("fill", "url(#gradient)");

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")");

    svg.append("path")
        .attr("class", "line")
        .attr("clip-path", "url(#clip)");

    x.domain([0, seqLength]);
    y.domain([0, d3.max(data, function(d) { return d.coverage; })]);
    
    scoreExtent = d3.extent(readData, function(d) { return d.score });
    scoreExtent[1] = (scoreExtent[1] > 1e-4 ? scoreExtent[1]:1e-4);
    colorScale.domain(scoreExtent);
    
    svg.append("rect")
        .attr("class", "pane")
        .attr("width", width)
        .attr("height", height)
        .call(zoom);

    svg.selectAll('.read')
        .data(readData)
      .enter().append("rect")
        .attr("class", "read")
        .style("fill", function(d) { return colorScale(d.score)})
        .style("stroke","#666666")
        .attr("clip-path", "url(#clip)")
        .append('svg:title')
        .text(function(d) { return d.name+", "+d.score })
        .filter( function(d) {
            if ((x(100) - x(0)) > width*0.1) {
                this.classList.remove('hidden');
                return true;
            } else {
                this.classList.add('hidden');
                return false;
            }
        })
        .attr("x", function(d) { return x(d.startPos); })
        .attr("y", function(d) { return y(d.depth); })
        .attr("width", function(d) { return x(d.endPos) - x(d.startPos); })
        .attr("height", function(d) { return (y(0)-y(1)); })
        .call(zoom);

    zoom.x(x);

    svg.select("path.area").data([data]);
    svg.select("path.line").data([data]);
    draw();

    function draw(e) {
    
    
        var yExtent = [0, d3.max(readData.filter( function(d) {
            if ((x(d.startPos) > width) || (x(d.endPos) < 0)) {
                return false;
            } else {
                return true;
            }
        }), function(d) { return d.depth })];
        var viewedYExtent = yExtent;
        if (yExtent[1] < 20 || !yExtent[1]) { 
            viewedYExtent[1] = 20;
        } else if (yExtent[1] > 50 && (x(100) - x(0)) > levelOfDetail) {
            if (d3.event.sourceEvent.shiftKey) {
                yExtentOffset += -d3.event.sourceEvent.deltaX/5
                yExtentOffset = (yExtentOffset < 0 ? 0:yExtentOffset);
            }
            viewedYExtent[0] = yExtentOffset;
            viewedYExtent[1] = 50 + yExtentOffset;
        }
        if ((x(100) - x(0)) < levelOfDetail) {
            yExtentOffset = 0;
        }
        y.domain(viewedYExtent);

        svg.selectAll("rect.read")
            .filter( function(d) {
                if ((x(100) - x(0)) > levelOfDetail) {
                    this.classList.remove('hidden');
                    return true;
                } else {
                    this.classList.add('hidden');
                    return false;
                }
            })
            .filter( function(d) {
                if ((x(d.startPos) > width) || (x(d.endPos) < 0)) {
                    this.classList.add('hidden')
                    return false;
                } else {
                    this.classList.remove('hidden')
                    return true;
                }
            })
            .filter( function(d) {
                if ((viewedYExtent[0] < d.depth) && (d.depth < viewedYExtent[1]+1)) {
                    this.classList.remove('hidden')
                    return true;
                } else {
                    this.classList.add('hidden')
                    return false;
                }
            })
            .attr("class", "read")
            .attr("x", function(d) { return x(d.startPos); })
            .attr("y", function(d) { return y(d.depth); })
            .attr("width", function(d) { return x(d.endPos) - x(d.startPos); })
            .attr("height", function(d) { return (y(0)-y(1)); })
            .attr("clip-path", "url(#clip)")
            .call(zoom);
            


        svg.select("g.x.axis").call(xAxis);
        svg.select("g.y.axis").transition().duration(200).ease("sin-in-out").call(yAxis);
        svg.select("path.area").attr("d", area);
        svg.select("path.line").attr("d", line);
    }    
               
    $('#coverageSvg').show();
    $('#geneTabs li:eq(1) a').tab('show');
}

$('#sunburst_options').click(function(e) {
    e.preventDefault();
    var link = $("#sunburst_options").parent(),
        sidebar = $("#optionsPane");
    if (link.hasClass("active")) {
        link.removeClass("active");
        sidebar.fadeOut();
    } else {
        link.addClass("active");
        sidebar.fadeIn();
    };
});

