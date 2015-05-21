$(document).ready(function() {
	
    $("#owl-demo").owlCarousel({
        stagePadding: 50,
        loop:true,
        items:3,
	    autoPlay: 4000,
	    navigation : false, // Show next and prev buttons
        slideSpeed : 700,
        paginationSpeed : 600,
	  });
    var $chart_target = $("#google_page_insite_chart");
    if($chart_target.length > 0){
        var nvd3_json = $chart_target.data("json");
        nv.addGraph(function() {

        var chart = nv.models.pieChart()
          .x(function(d) { return d.label })
          .y(function(d) { return d.value })
          .labelType("percent")
          .donut(true)
          .donutRatio(0.35);

        d3.select("#google_page_insite_chart svg")
            .datum(nvd3_json)
          .transition().duration(1200)
            .call(chart);

        return chart;
        });

    }

});

(function () {
    'use strict';

    var website = openerp.website;
    website.if_dom_contains('#o_responsive_mockup_screens', function() {

        function genrate_screenshot(type){
            var id = $("." + type + " .img_loader").data('id');
            var src = $("." + type + " .img_loader").data('src');
            openerp.jsonRpc('/websites/genrate_screenshot/'+id, 'call', {
                type: type,
            }).then(function(data){
                $("." + type + " .screen").attr('src',src);
                $("." + type + " .img_loader").remove();
            });
        }
        if($(".desktop .img_loader").length > 0){
            setTimeout(function(){
                genrate_screenshot('desktop');
            }, 1);
        }
        if($(".laptop .img_loader").length > 0){
            setTimeout(function(){
                genrate_screenshot('laptop');
            }, 2200);
        }
        if($(".tablet .img_loader").length > 0){
            setTimeout(function(){
                genrate_screenshot('tablet');
            }, 4200);
        }
        if($(".mobile .img_loader").length > 0){
            setTimeout(function(){
                genrate_screenshot('mobile');
            }, 6600);
        }
    });

})();