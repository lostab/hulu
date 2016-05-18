$(document).ready(function(){   
    $(".itemcontent-content").each(function(){
        $(this).html($(this).html().replace(/((http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-\|]*[\w@?^=%&amp;\/~+#-\|])?)/g, "<a href=\"$1\" target=\"_blank\">$1</a>"));
    });
    $(".itemcontent-content a").each(function(){
        var url = $(this).text();
        var urlitem = $(this);
        $("<img>", {
            src: url,
            load: function() {
                urlitem.after($(this));
                urlitem.remove();
            },
            error: function() {
                
            }
        });
    });
    $("form").each(function(){
        $(this).submit(function(){
            $(this).find(".submit").attr("disabled", true);
        });
    });
    var svgresize = function(){
        $("svg").each(function(){
            if ($(this).attr("owidth").split("pt")[0] * 4 / 3 > $(this).parent().width() || $(this).attr("width") > $(this).parent().width() || ($(this).attr("owidth").split("pt")[0] * 3 / 4 > $(this).parent().width() && $(this).attr("width") < $(this).parent().width())) {
                $(this).attr("height", $(this).parent().width() * ($(this).attr("oheight").split("pt")[0] / $(this).attr("owidth").split("pt")[0]));
                $(this).attr("width", $(this).parent().width());
            }
        });
    }
    $("svg").each(function(){
        $(this).attr("owidth", $(this).attr("width"));
        $(this).attr("oheight", $(this).attr("height"));
    });
    svgresize();
    $(window).resize(function() {
        svgresize();
    });
    $(".container").css({"min-height": "calc(100% - " + ($(".header").height() + 12 + $(".footer").height()) + "px - " + $(".container").css("padding-top") + ")"});
});
