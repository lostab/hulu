$(document).ready(function(){
    $(".itemcontent-content pre, .userprofile pre, .userpage pre").each(function(){
        //$(this).html($(this).html().replace(/((http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-\|]*[\w@?^=%&amp;\/~+#-\|])?)/g, "<a href=\"$1\" target=\"blank\">$1</a>"));
        $(this).html($(this).html().replace(/([a-zA-z]+\:\/\/[^\s]*)/g, "<a href=\"$1\" target=\"blank\">$1</a>"));
    });
    $(".itemcontent-content a, .userprofile .description a, .userpage .description a").each(function(){
        var url = $(this).text();
        var urlitem = $(this);
        $("<img>", {
            src: url
        }).on("load", function() {
            urlitem.after($(this));
            urlitem.remove();
        }).on("error", function() {

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

        if($(window).width() > 720 && $(".sidebar").height() + 70 > $(window).height()) {
            $(".sidebar").css({"position": "absolute"});
            $(".container").css({"min-height": "calc(100% - " + ($(".header").height() - 46 + $(".footer").height() - $(".sidebar").height() - 70 + $(window).height()) + "px - " + $(".container").css("padding-top") + ")"});
        } else {
            if ($(window).width() > 720) {
                $(".sidebar").css({"position": "fixed"});
            } else {
                $(".sidebar").css({"position": "relative"});
            }
            $(".container").css({"min-height": "calc(100% - " + ($(".header").height() - 46 + $(".footer").height()) + "px - " + $(".container").css("padding-top") + ")"});
        }
    }
    $("svg").each(function(){
        $(this).attr("owidth", $(this).attr("width"));
        $(this).attr("oheight", $(this).attr("height"));
    });
    svgresize();
    $(window).resize(function() {
        svgresize();
    });
    $(".container").css({"min-height": "calc(100% - " + ($(".header").height() - 46 + $(".footer").height()) + "px - " + $(".container").css("padding-top") + ")"});
    $(".header .search").css({"width": "calc(100% - " + ($(".header .logo").width() + $(".header .right-navbar").width() + 24) + "px)", "margin-right": ($(".header .right-navbar").width() + 16) + "px"});

    $(".itemform .submit").click(function(){
        if($.trim($(this).closest(".itemform").find("textarea").val()) == "") {
            $(this).closest(".itemform").find("textarea").focus();
            return false;
        } else {
            if(window.localStorage){
                localStorage.removeItem("itemcontent");
            }
        }
    });

    if(window.localStorage){
        var ls = localStorage.getItem("itemcontent");
        if($(".itemform").find("textarea").val() == "" && ls != null && ls != ""){
            $(".itemform").find("textarea").val(ls);
        }
        $(".itemform").find("textarea").on("input propertychange paste change", function(){
            localStorage.setItem("itemcontent", $(".itemform").find("textarea").val());
        });
    }

    if ($('html').attr('lang') == "zh") {
        $(".itemform .submit").parent().before('\
            <div class="fileselect" style="text-align: center;">\
                <input class="wbimg" type="file" name="file" style="display: none;" />\
                <input class="fileselectbutton" type="button" value="上传图片" style="font-size: small;" />\
            </div>\
            <div class="process" style="width: 100%; display: none;">\
                <div class="processbar" style="width: 0%; height: 22px; background: black;"></div>\
            </div>\
            <div class="uploadinfo" style="text-align: center; height: 18px; font-size: small; color: gray;"></div>\
        ');
    } else {
        $(".itemform .submit").parent().before('\
            <div class="fileselect" style="text-align: center;">\
                <input class="wbimg" type="file" name="file" style="display: none;" />\
                <input class="fileselectbutton" type="button" value="Upload Image" style="font-size: small;" />\
            </div>\
            <div class="process" style="width: 100%; display: none;">\
                <div class="processbar" style="width: 0%; height: 22px; background: black;"></div>\
            </div>\
            <div class="uploadinfo" style="text-align: center; height: 18px; font-size: small; color: gray;"></div>\
        ');
    }
    $(".itemform .fileselectbutton").click(function(){
        $(this).closest(".itemform").find(".wbimg").click();
    });
    $(".itemform .wbimg").fileupload({
        url: "/wi/",
        dataType: "jsonp",
        done: function(e, data){
            $(this).prop("disabled", false);
            $(this).next(".fileselectbutton").prop("disabled", false);
            $(this).parent().show();
            $(this).closest(".itemform").find(".submit").prop("disabled", false);
            var wbimgurl = data.result.original_pic;
            if ($(this).closest(".itemform").find("textarea").val() == "") {
                $(this).closest(".itemform").find("textarea").val(wbimgurl);
            } else {
                $(this).closest(".itemform").find("textarea").val($(this).closest(".itemform").find("textarea").val() + "\r\n" + wbimgurl);
            }
            $(this).closest(".itemform").find(".process").hide();
            $(this).closest(".itemform").find(".uploadinfo").show();
            if ($('html').attr('lang') == "zh") {
                $(this).closest(".itemform").find(".uploadinfo").text("上传成功，请备份图片链接。");
            } else {
                $(this).closest(".itemform").find(".uploadinfo").text("Upload succeeded, please backup the link.");
            }

        },
        fail: function(e, data){
            $(this).prop("disabled", false);
            $(this).next(".fileselectbutton").prop("disabled", false);
            $(this).parent().show();
            $(this).closest(".itemform").find(".submit").prop("disabled", false);
            $(this).closest(".itemform").find(".process").hide();
            $(this).closest(".itemform").find(".uploadinfo").show();
            if ($('html').attr('lang') == "zh") {
                $(this).closest(".itemform").find(".uploadinfo").text("上传失败，请检查图片后重试。");
            } else {
                $(this).closest(".itemform").find(".uploadinfo").text("Upload failed, please check and retry.");
            }
        },
        progressall: function(e, data){
            $(this).closest(".itemform").find(".process").show();
            //$(this).closest(".itemform").find(".uploadinfo").hide();
            var process = parseInt(data.loaded / data.total * 100, 10);
            $(this).closest(".itemform").find(".process .processbar").css("width", process + "%");
            $(this).closest(".itemform").find(".uploadinfo").text(process + "%");
        },
        add: function(e, data){
            $(this).prop("disabled", true);
            $(this).next(".fileselectbutton").prop("disabled", true);
            $(this).parent().hide();
            $(this).closest(".itemform").find(".submit").prop("disabled", true);
            //$(this).closest(".itemform").find(".process").hide();
            $(this).closest(".itemform").find(".uploadinfo").show();
            if ($('html').attr('lang') == "zh") {
                $(this).closest(".itemform").find(".uploadinfo").text("正在上传…");
            } else {
                $(this).closest(".itemform").find(".uploadinfo").text("uploading...");
            }
            data.submit();
        }
    });

    $(".newtagform").submit(function(){
        var itemtag = $(this).find(".item-tag-name");
        if ( itemtag.val() == "") {
            itemtag.focus();
            $(".newtagform .submit").attr("disabled", false);
            return false;
        }
    });

    $(".search").submit(function(){
        var qstr = $(this).find(".qstr");
        if (qstr.val() == "") {
            qstr.focus();
            return false;
        }
    });
    /*
    $(".search .qstr").attr("placeholder", "搜索并播放歌曲");
    $(".search").submit(function(){
        var qstr = $(this).find(".qstr");
        if (qstr.val() == "") {
            qstr.focus();
            return false;
        } else {
            $.ajax({
                type: "get",
                url: "https://c.y.qq.com/soso/fcgi-bin/search_cp?remoteplace=txt.yqq.center&searchid=53956420086125571&t=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=20&w=" + qstr.val() + "&g_tk=938407465&jsonpCallback=searchCallbacksong1662&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0",
                dataType: "jsonp",
                jsonpCallback:"searchCallbacksong1662",
                success: function(data){
                    var songmid = data.data.song.list[0].songmid;
                    if(songmid != ""){
                        $.ajax({
                            type: "get",
                            url: "https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?songmid=" + songmid + "&tpl=yqq_song_detail&format=jsonp&callback=getOneSongInfoCallback&g_tk=938407465&jsonpCallback=getOneSongInfoCallback&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0",
                            dataType: "jsonp",
                            jsonpCallback:"getOneSongInfoCallback",
                            success: function(data){
                                var url = "";
                                for(i in data.url){
                                    url = data.url[i];
                                }
                                if (url != ""){
                                    var info = data.data[0].singer[0].name + " - " + data.data[0].title;
                                    if (url != "" && $("body").length > 0) {
                                        if ($("body .musicplayer").length > 0){
                                            $(".search .musicswitch").remove();
                                            $("body .musicplayer").remove();
                                        }
                                        qstr.attr("placeholder", info);
                                        $("body").append("<div class=\"musicplayer\"><audio autoplay=\"autoplay\" controls=\"controls\" loop=\"loop\" preload=\"preload\" style=\"width: 100%;display: none;\" src=\"http://" + url + "\">浏览器不支持</audio></div>");
                                        $(".search").append("<a class=\"musicswitch\"></a>");
                                        $(".search .musicswitch").css({
                                            "font-family": "arial,sans-serif",
                                            "color": "white",
                                            "background": "green",
                                            "font-weight": "bold",
                                            "width": "24px",
                                            "height": "24px",
                                            "line-height": "24px",
                                            "border-radius": "12px",
                                            "-webkit-border-radius": "12px",
                                            "-moz-border-radius": "12px",
                                            "text-align": "center",
                                            "font-size": "small",
                                            "display": "inline-block",
                                            "position": "absolute",
                                            "right": "-3px",
                                            "top": "0px",
                                            "cursor": "pointer",
                                            "opacity": "0.6",
                                            "filter": "alpha(opacity=60)"
                                        });
                                        $(".search .musicswitch").mouseover(function(){
                                            $(this).css({
                                                "opacity": "1",
                                                "filter": "alpha(opacity=100)"
                                            });
                                        }).mouseout(function(){
                                            $(this).css({
                                                "opacity": "0.6",
                                                "filter": "alpha(opacity=60)"
                                            });
                                        });

                                        var getplaystatus = function(){
                                            if($("body .musicplayer audio")[0].paused){
                                                $(".search .musicswitch").text("开");
                                            } else {
                                                $(".search .musicswitch").text("关");
                                            }
                                            setTimeout(getplaystatus, 1000);
                                        }
                                        getplaystatus();

                                        $(".search .musicswitch").click(function(){
                                            if($(this).text() == "关"){
                                                $("body .musicplayer audio")[0].pause();
                                                $(this).text("开");
                                            } else if ($(this).text() == "开") {
                                                $("body .musicplayer audio")[0].play();
                                                $(this).text("关");
                                            }
                                        });

                                        $("body .musicplayer audio").on("error", function() {
                                            if ($("body .musicplayer").length > 0){
                                                $(".search .musicswitch").remove();
                                                $("body .musicplayer").remove();
                                            }
                                            qstr.attr("placeholder", "没有找到");
                                            $(".search .musicswitch").remove();
                                            $("body .musicplayer").remove();
                                        });
                                    } else {
                                        qstr.attr("placeholder", "没有找到");
                                        $(".search .musicswitch").remove();
                                        $("body .musicplayer").remove();
                                    }
                                } else {
                                    qstr.attr("placeholder", "没有找到");
                                    $(".search .musicswitch").remove();
                                    $("body .musicplayer").remove();
                                }
                            },
                            error: function(){
                                qstr.attr("placeholder", "没有找到");
                                $(".search .musicswitch").remove();
                                $("body .musicplayer").remove();
                            }
                        });
                    } else {
                        qstr.attr("placeholder", "没有找到");
                        $(".search .musicswitch").remove();
                        $("body .musicplayer").remove();
                    }
                },
                error: function(){
                    qstr.attr("placeholder", "没有找到");
                    $(".search .musicswitch").remove();
                    $("body .musicplayer").remove();
                }
            });
            qstr.val("");
            return false;
        }
    });
    */
});
