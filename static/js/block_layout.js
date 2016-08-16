//js for block layout
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




















