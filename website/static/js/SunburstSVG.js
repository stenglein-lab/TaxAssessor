d3.selection.prototype.moveToFront = function() {
  return this.each(function(){
    this.parentNode.appendChild(this);
  });
};
d3.selection.prototype.moveToBack = function() { 
    return this.each(function() { 
        var firstChild = this.parentNode.firstChild; 
        if (firstChild) { 
            this.parentNode.insertBefore(this, firstChild); 
        } 
    }); 
};

var taxTreeJson = "../../docs/"+$('#username').attr("value")+"/"+
  $('#open-file').attr("value")+"_tree.json";

var width = 1000,
    height = 700,
    duration = 750,
    radius = Math.min(width,height)/2,
    maxShowDepth = 1000;
    maxDepth = 0,
    currentDepth = 0;

var formatNumber = d3.format(",d")

var x = d3.scale.linear()
    .range([0,2*Math.PI]);
var y = d3.scale.sqrt()
    .range([0,radius]);

var color = d3.scale.category20c();

var svg = d3.select("#chart").append("div")
    .classed("svg-container",true)
  .append("svg")
    .attr("preserveAspectRatio","xMinYMin meet")
    .attr("viewBox","0 0 "+width+" "+height)
  .append("g")
    .attr("transform", "translate(" + width / 2 + "," + (height / 2) + ")");
      
var partition = d3.layout.partition()
    .value(function(d) { return d.size; });

var arc = d3.svg.arc()
    .startAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x))); })
    .endAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, x(d.x + d.dx))); })
    .innerRadius(function(d) { return Math.max(0, y(d.y)*scaleArcRadius(d)); })
    .outerRadius(function(d) { return Math.max(0, y(d.y + d.dy)*scaleArcRadius(d)); });
    
d3.json(taxTreeJson, function(error, root) {
    if (error) throw error;

    filterByAbundance(root,root.size);    
    partition.nodes(root);
    accordianData(root,null);
    startColors(root);
    assignColor(root);
    findMaxDepth(root);
    
    var g1 = svg.selectAll("path")
        .data(partition.nodes(root))
      .enter().append('g');
      
    var g2 = svg.selectAll("path")
        .data(partition.nodes(root))
      .enter().append('g');
      
    var path = g1.append("path")
        .attr("d", arc)
        .style("fill", function(d) { return d.color; })
        .on("click", click)
      
    var titles = path.append("title")
        .text(function(d) { return d.name + "\n" + formatNumber(d.value); });
        
    var text = g2.append("text")
        .style("font-size", "10px")
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
        .text(SetTextText)
        .attr("pointer-events","none");
            
    function SetTextAnchor(d) {
        //console.log(d);
        if (d.children) {
            //console.log("middle");
            return "middle";
        } else {
            if (arc.centroid(d)[0] >= 0) {
                //console.log("start");
                return "start";
            } else {
                //console.log("end");
                return "end";
            }            
        }
    }  
         
    function SetTextText(d) {
        //console.log(d);
        if (d.children) {
            if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.5) {
                if (d.depth <= currentDepth + 2) {
                    return d.name;
                } else {
                    return null;
                }
            } else {
                return null;
            }
        } else {
            if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.05) {
                return d.name
            } else {
                return null
            }
        }
    }       
                
    function getAngle(d) {
        if (d.children) {
            var thetaDeg = (180 / Math.PI * (arc.startAngle()(d) + arc.endAngle()(d)) / 2 );
            return (thetaDeg > 90 && thetaDeg < 280) ? thetaDeg - 180 : thetaDeg;
        } else {
            var thetaDeg = (180 / Math.PI * (arc.startAngle()(d) + arc.endAngle()(d)) / 2 - 90);
            return (thetaDeg > 90) ? thetaDeg - 180 : thetaDeg;        
        }

    }

    function click(d) {
        currentDepth = d.depth
        var trans = svg.transition()
            .duration(duration)
            .tween("scale", function() {
                var xd = d3.interpolate(x.domain(), [d.x, d.x + d.dx]),
                    yd = d3.interpolate(y.domain(), [d.y, 1]),
                    yr = d3.interpolate(y.range(), [d.y ? 20 : 0, radius]);
                return function(t) { x.domain(xd(t)); y.domain(yd(t)).range(yr(t)); };
            })
            
        trans.selectAll("path")
            .attrTween("d", function(d) { return function() { return arc(d); }; });

        trans.selectAll('.label')
            .attrTween("transform", function(d) { return function () {
                return "translate(" + arc.centroid(d) + ")" + "rotate(" + getAngle(d) + ")";}})
            .attrTween("text-anchor", function(d) { return function () { return SetTextAnchor(d)}})
            .tween("text", function(d) { 
                return function() {
                    if (d.children) {
                        if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.5) {
                            if (currentDepth-1 <= d.depth && d.depth <= currentDepth + 2) {
                                this.textContent = d.name;
                            } else {
                                this.textContent =  null;
                            }
                        } else {
                            this.textContent =  null;
                        }
                    } else {
                        if ((arc.endAngle()(d) - arc.startAngle()(d)) > 0.05) {
                            this.textContent =  d.name;
                        } else {
                            this.textContent =  null;
                        }
                    }
                }
            });
    }
        
});
    

function filterByAbundance(d,maxVal) {
    if (d.children) {
        var i = d.children.length
        while (i--) {
            if (d.children[i].size/maxVal < 0.0001) {
                d.children.splice(i,1);
            } else {
                filterByAbundance(d.children[i],maxVal);
            }
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
        return 1
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




