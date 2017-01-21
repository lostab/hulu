var ajaxloadpage = function(url, data){
    $("body").html("");
    if (url == "/m/" || window.location.pathname == "/m/") {
        $("head").find("link").remove();
        $(data).filter("link").appendTo("head");
        setTimeout(function(){
            $(data).filter(".wrapper").appendTo("body");
        }, 0);
        setTimeout(function(){
            $(data).filter("script").appendTo("body");
        }, 0);
    } else {
        $(data).filter(".wrapper").appendTo("body");
        $(data).filter("script").appendTo("body");
    }
    $("html,body").animate({scrollTop:0}, 0);
    window.history.pushState({
        "url": window.location.href,
        "pathname": window.location.pathname,
        "title": document.title
    }, $(data).filter("title").text(), url);
    document.title = $(data).filter("title").text();
}

var ajaxload = function(url){
    if($(".header .ajaxloading").length == 0) {
        $(".header").append("<div class=\"ajaxloading\"><span></span></div>");
        $.get(url, function(data){
            ajaxloadpage(url, data);
        }, "html");
    }
}

var ajaxget = function(obj){
    if(window.history && window.history.pushState) {
        obj.click(function(e){
            //e.preventDefault();
            var thus = $(this);
            var event_obj = $._data(thus[0], "events");
            if (event_obj && event_obj["click"] && event_obj["click"].length > 1) {

            } else {
                if (thus.attr("href") && !thus.hasClass("oauthbtn") && (thus.attr("href").split("//").length == 1 || (thus.attr("href").split("//").length > 1 && thus.attr("href").split("//")[1].split("/")[0] == window.location.host))) {
                    ajaxload(thus.attr("href"));
                    return false;
                }
            }
        });
    }
}

var ajaxpost = function(obj){
    if(window.history && window.history.pushState) {
        obj.submit(function(e){
            e.preventDefault();
            var thus = $(this);
            if(thus.attr("action")){
                var url = thus.attr("action");
            } else {
                var url = window.location.href;
            }
            var event_obj = $._data(thus[0], "events");
            //if (event_obj && event_obj["submit"] && event_obj["submit"].length > 1) {

            //} else {
            if(thus.attr("method") && thus.attr("method").toLowerCase() == "post" && !thus.hasClass("additemtag")){
                if($(".header .ajaxloading").length == 0) {
                    $(".header").append("<div class=\"ajaxloading\"><span></span></div>");
                    $.post(url, obj.serialize(), function(data, status, xhr){
                        if ($(data).filter("meta[name=uri]") && $(data).filter("meta[name=uri]").attr("content")){
                            var url = $(data).filter("meta[name=uri]").attr("content");
                            ajaxloadpage(url, data);
                        }
                    }, "html");
                }
            }
        });
    }
}

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
                setTimeout(function(){
                    $(data).filter("script").appendTo("body");
                }, 0);
            } else {
                $(data).filter(".wrapper").appendTo("body");
                $(data).filter("script").appendTo("body");
            }
            $("html,body").animate({scrollTop:0}, 0);
            document.title = $(data).filter("title").text();
        }, "html");
    }, false);
    window.isaddpopstateevent = true;
}
