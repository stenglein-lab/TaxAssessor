// Get JSON data
treeJSON = d3.json("../javascript/tree.json", function(error, treeData) {

    var i = 0;

    var margin = {top: 20, right: 120, bottom: 20, left: 120},
        width = 4000 - margin.right - margin.left,
        height =1200 - margin.top - margin.bottom;
        //width = $(document).width(),
        //height = $(document).height();
        console.log(width)
        console.log(height)
   
    var tree = d3.layout.tree()
        .size([height, width]); 
    
    var diagonal = d3.svg.diagonal()
        .projection(function(d) { return [d.y, d.x]; });
    
    var svg = d3.select("body")
        .append("svg")
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var menu = [
        {title: 'Item #1',
        action: function(d) {
            console.log('Item #1 clicked!');}},
        {title: 'Item #2',
        action: function(d) {
            console.log('You have clicked the second item!');}}]

    root = treeData;

    function toggleAll(d) {
        if (d.children) {
            d.children.forEach(toggleAll);
            toggle(d);
        }
    }

    function toggle(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
    }

    root.children.forEach(toggleAll);

    update(root);
    
    function update(source) {

        var duration = d3.event && d3.event.altKey ? 5000 : 500;
    
        var nodes = tree.nodes(root);
            
        nodes.forEach(function(d) { d.y = d.depth * 200; });
    
        var node = svg.selectAll("g.node")
            .data(nodes, function(d) { return d.id || (d.id = ++i); })  ;      
            
        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) { 
                return "translate(" + source.y0 + "," + source.x0 + ")"; })
            .on("click", function(d) { toggle(d); update(d); });

        nodeEnter.append("circle")
            .attr("r",1)
            .style("fill", function(d) { 
                return d.children ? "lightsteelblue" : "#fff"; });
    
        nodeEnter.append("text")
    //        .attr("x", function(d) { 
    //            return d.children || d._children ? -13 : 13; })
            .attr("x",-14)
            .attr("dy", "0em")
    //        .attr("text-anchor", function(d) { 
    //            return d.children || d._children ? "end" : "start"; })
            .attr("text-anchor","end")
            .text(function(d) { return d.name; })
            .style("fill-opacity", 1);
            
        nodeEnter.append("text")
    //        .attr("x", function(d) { 
    //            return d.children || d._children ? -13 : 13; })
            .attr("x",-14)
            .attr("dy", "1em")
    //        .attr("text-anchor", function(d) { 
    //            return d.children || d._children ? "end" : "start"; })
            .attr("text-anchor","end")
            .text(function(d) { return (d.size).toFixed(2); })
            .style("fill-opacity", 1);
    
        var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });


        nodeUpdate.select("circle")
            .attr("r", function(d) { size = 12*(d.size/root.size);
                                     return size>4 ? size: 4; })
            .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

        nodeUpdate.select("text")
            .style("fill-opacity", 1);

        // Transition exiting nodes to the parent's new position.
        var nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function(d) { 
                return "translate(" + source.y + "," + source.x + ")"; 
            })
            .remove();

        nodeExit.select("circle")
            .attr("r", 1e-6);

        nodeExit.select("text")
            .style("fill-opacity", 1e-6);
    
        //Update the links
        var link = svg.selectAll("path.link")
            .data(tree.links(nodes), function(d) { return d.target.id; });
        
        //Enter any new links at the parent's previous position.
        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", function(d) {
                var o = {x: source.x0, y: source.y0};
                return diagonal({source: o, target: o});
            })
            .transition()
            .duration(duration)
            .attr("d", diagonal);

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
        
        svg.selectAll('circle')
            .on('contextmenu', d3.contextMenu(menu));
    }

});