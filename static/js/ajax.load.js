var ajaxload = function(){
    if(window.history && window.history.pushState) {
        $("a").click(function(e){
            var thus = $(this);
            var event_obj = $._data(thus[0], "events");
            if (event_obj && event_obj["click"] && event_obj["click"].length > 1) {

            } else {
                if (thus.attr("href") && (thus.attr("href").split("//").length == 1 || (thus.attr("href").split("//").length > 1 && thus.attr("href").split("//")[1].split("/")[0] == window.location.host))) {
                    if($(".header .ajaxloading").length == 0) {
                        $(".header").append("<div class=\"ajaxloading\"><span></span></div>");
                        $.get(thus.attr("href"), function(data){
                            e.preventDefault();
                            $("body").html("");
                            if (thus.attr("href") == "/m/" || window.location.pathname == "/m/") {
                                $("head").find("link").remove();
                                $(data).filter("link").appendTo("head");
                                setTimeout(function(){
                                    $(data).filter(".wrapper").appendTo("body");
                                }, 0);
                            } else {
                                $(data).filter(".wrapper").appendTo("body");
                            }
                            setTimeout(function(){
                                $(data).filter("script").appendTo("body");
                            }, 0);

                            $("html,body").animate({scrollTop:0}, 0);
                            window.history.pushState({
                                "url": window.location.href,
                                "pathname": window.location.pathname,
                                "title": document.title
                            }, $(data).filter("title").text(), thus.attr("href"));
                            document.title = $(data).filter("title").text();
                        }, "html");
                    }
                    return false;
                }
            }
        });

        if(!window.isaddpopstateevent){
            window.addEventListener("popstate", function(e){
                $.get(window.location.href, function(data){
                    $("body").html("");
                    if ((e.state && e.state.pathname == "/m/") || window.location.pathname == "/m/") {
                        $("head").find("link").remove();
                        $(data).filter("link").appendTo("head");
                        setTimeout(function(){
                            $(data).filter(".wrapper").appendTo("body");
                        }, 0);
                    } else {
                        $(data).filter(".wrapper").appendTo("body");
                    }

                    setTimeout(function(){
                        $(data).filter("script").appendTo("body");
                    }, 0);
                    $("html,body").animate({scrollTop:0}, 0);
                    document.title = $(data).filter("title").text();
                }, "html");
            }, false);
            window.isaddpopstateevent = true;
        }
    }
}
