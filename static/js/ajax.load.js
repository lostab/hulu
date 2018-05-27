var showtips = function(text){
    $("body .tips").remove();
    $("body").append("<div class=\"tips\" style=\"z-index: 999;border: 1px solid lightgray;width: 180px;min-height: 22px;line-height: 22px;top: 3px;left: 50%;margin-left: -91px;position: fixed;background: lightyellow;color: black;cursor: pointer;text-align: center;border-radius: 3px;-webkit-border-radius: 3px;-moz-border-radius: 3px;\">" + text + "</div>");
    $("body .tips").click(function(){
        $(this).remove();
    });
};

var ajaxloadpage = function(url, data){
    var locationhostname = window.location.pathname;
    window.history.pushState({
        "url": window.location.href,
        "pathname": window.location.pathname,
        "title": document.title
    }, $(data).filter("title").text(), url);
    document.title = $(data).filter("title").text();
    $(".wrapper").remove();
    if (url == "/m/" || locationhostname == "/m/" || url.split("/")[3] == "m") {
        $("head").find("link").remove();
        $(data).filter("link").appendTo("head");
        setTimeout(function(){
            $(data).filter(".wrapper").appendTo("body");
        }, 0);
    } else {
        $(data).filter(".wrapper").appendTo("body");
    }
    $("html,body").animate({scrollTop:0}, 0);
    $("body .ajaxloading").remove();
}

var ajaxload = function(url){
    $("body .tips").remove();

    if($("body .ajaxloading").length == 0) {
        //$(".header").append("<div class=\"ajaxloading\"><span></span></div>");
        $(".wrapper").after($("<div class=\"ajaxloading\" style=\"background:lightgray;opacity:0.8;top:0;position:fixed;z-index:999;width:100%;height:100%;margin:0;padding:0;vertical-align:middle;\"><div class=\"loading-content\" style=\"text-align:center;width:100%;height:32px;position:absolute;top:50%;margin-top:-16px;\"><!--<span style=\"\">" + (($('html').attr('lang') == "zh")?"加载中…":"loading...") + "</span>--><img src=\"/s/loading.gif\" style=\"width: 32px;height: 32px;\" /></div></div>"));
        $.ajaxSetup({
            cache: true
        });
        $.ajax({
            type: "GET",
            url: url,
            success: function(data){
                //ajaxloadpage(url, data);
                if ($(data).filter("meta[name=uri]") && $(data).filter("meta[name=uri]").attr("content")){
                    var url = $(data).filter("meta[name=uri]").attr("content");
                    ajaxloadpage(url, data);
                } else {
                    ajaxloadpage(url, data);
                }
            },
            dataType: "html",
            error: function(){
                //$(".header .ajaxloading").remove();
                $("body .ajaxloading").remove();
                showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
            },
            //timeout: 7000,
            complete : function(XMLHttpRequest, status){
                if(status=='timeout'){
                    $("body .ajaxloading").remove();
                    showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                }
            }
        });
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

            //}
            if(thus.attr("method") && thus.attr("method").toLowerCase() == "post"){
                $("body .tips").remove();

                if($("body .ajaxloading").length == 0) {
                    //$(".header").append("<div class=\"ajaxloading\"><span></span></div>");
                    $(".wrapper").after($("<div class=\"ajaxloading\" style=\"background:lightgray;opacity:0.8;top:0;position:fixed;z-index:999;width:100%;height:100%;margin:0;padding:0;vertical-align:middle;\"><div class=\"loading-content\" style=\"text-align:center;width:100%;height:32px;position:absolute;top:50%;margin-top:-16px;\"><!--<span style=\"\">" + (($('html').attr('lang') == "zh")?"加载中…":"loading...") + "</span>--><img src=\"/s/loading.gif\" style=\"width: 32px;height: 32px;\" /></div></div>"));

                    var submitformData = new FormData(thus[0]);
                    submitformData.append("csrfmiddlewaretoken", thus.find('[name="csrfmiddlewaretoken"]').val());

                    $.ajaxSetup({
                        cache: true
                    });
                    $.ajax({
                        type: "POST",
                        url: url,
                        //data: thus.serialize(),
                        data: submitformData,
                        contentType: false,
                        processData: false,
                        success: function(data, status, xhr){
                            if ($(data).filter("meta[name=uri]") && $(data).filter("meta[name=uri]").attr("content")){
                                var url = $(data).filter("meta[name=uri]").attr("content");
                                ajaxloadpage(url, data);
                            } else {
                                ajaxloadpage(url, data);
                            }
                        },
                        dataType: "html",
                        error: function(){
                            //$(".header .ajaxloading").remove();
                            $("body .ajaxloading").remove();
                            showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                        },
                        //timeout: 7000,
                        complete : function(XMLHttpRequest, status){
                            if(status=='timeout'){
                                $("body .ajaxloading").remove();
                                showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                            }
                        }
                    });
                }
            }
            if(thus.attr("method") && thus.attr("method").toLowerCase() == "get"){
                $("body .tips").remove();

                if($("body .ajaxloading").length == 0) {
                    //$(".header").append("<div class=\"ajaxloading\"><span></span></div>");
                    $(".wrapper").after($("<div class=\"ajaxloading\" style=\"background:lightgray;opacity:0.8;top:0;position:fixed;z-index:999;width:100%;height:100%;margin:0;padding:0;vertical-align:middle;\"><div class=\"loading-content\" style=\"text-align:center;width:100%;height:32px;position:absolute;top:50%;margin-top:-16px;\"><!--<span style=\"\">" + (($('html').attr('lang') == "zh")?"加载中…":"loading...") + "</span>--><img src=\"/s/loading.gif\" style=\"width: 32px;height: 32px;\" /></div></div>"));
                    $.ajaxSetup({
                        cache: true
                    });
                    $.ajax({
                        type: "GET",
                        url: url,
                        data: thus.serialize(),
                        success: function(data){
                            if ($(data).filter("meta[name=uri]") && $(data).filter("meta[name=uri]").attr("content")){
                                var url = $(data).filter("meta[name=uri]").attr("content");
                                ajaxloadpage(url, data);
                            } else {
                                ajaxloadpage(url, data);
                            }
                        },
                        dataType: "html",
                        error: function(){
                            //$(".header .ajaxloading").remove();
                            $("body .ajaxloading").remove();
                            showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                        },
                        //timeout: 7000,
                        complete : function(XMLHttpRequest, status){
                            if(status=='timeout'){
                                $("body .ajaxloading").remove();
                                showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                            }
                        }
                    });
                    return false;
                }
            }
        });
    }
}

if(window.history && window.history.pushState) {
    if(!window.isaddpopstateevent){
        window.addEventListener("popstate", function(e){
            $("body .tips").remove();

            //$(".header").append("<div class=\"ajaxloading\"><span></span></div>");
            $(".wrapper").after($("<div class=\"ajaxloading\" style=\"background:lightgray;opacity:0.8;top:0;position:fixed;z-index:999;width:100%;height:100%;margin:0;padding:0;vertical-align:middle;\"><div class=\"loading-content\" style=\"text-align:center;width:100%;height:32px;position:absolute;top:50%;margin-top:-16px;\"><!--<span style=\"\">" + (($('html').attr('lang') == "zh")?"加载中…":"loading...") + "</span>--><img src=\"/s/loading.gif\" style=\"width: 32px;height: 32px;\" /></div></div>"));
            $.ajaxSetup({
                cache: true
            });
            $.ajax({
                type: "GET",
                url: window.location.href,
                success: function(data){
                    document.title = $(data).filter("title").text();
                    $(".wrapper").remove();
                    if ((e.state && e.state.pathname == "/m/") || window.location.pathname == "/m/") {
                        $("head").find("link").remove();
                        $(data).filter("link").appendTo("head");
                        setTimeout(function(){
                            $(data).filter(".wrapper").appendTo("body");
                        }, 0);
                    } else {
                        $(data).filter(".wrapper").appendTo("body");
                    }
                    $("html,body").animate({scrollTop:0}, 0);
                    $("body .ajaxloading").remove();
                },
                dataType: "html",
                error: function(){
                    //$(".header .ajaxloading").remove();
                    $("body .ajaxloading").remove();
                    showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                },
                //timeout: 7000,
                complete : function(XMLHttpRequest, status){
                    if(status=='timeout'){
                        $("body .ajaxloading").remove();
                        showtips((($('html').attr('lang') == "zh")?"加载失败。":"Error loding."));
                    }
                }
            });
        }, false);
        window.isaddpopstateevent = true;
    }
}
