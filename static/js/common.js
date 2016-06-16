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
        $(".itemform").find("textarea").change(function(){
            localStorage.setItem("itemcontent", $(".itemform").find("textarea").val());
        });
    }
    
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
            $(this).closest(".itemform").find("textarea").val($(this).closest(".itemform").find("textarea").val() + " " + wbimgurl);
            $(this).closest(".itemform").find(".process").hide();
            $(this).closest(".itemform").find(".uploadinfo").show();
            $(this).closest(".itemform").find(".uploadinfo").text("上传成功，请记住图片链接。");
            
        },
        fail: function(e, data){
            $(this).prop("disabled", false);
            $(this).next(".fileselectbutton").prop("disabled", false);
            $(this).parent().show();
            $(this).closest(".itemform").find(".submit").prop("disabled", false);
            $(this).closest(".itemform").find(".process").hide();
            $(this).closest(".itemform").find(".uploadinfo").show();
            $(this).closest(".itemform").find(".uploadinfo").text("上传失败，请检查图片后重试。");
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
            $(this).closest(".itemform").find(".uploadinfo").text("正在上传…");
            data.submit();
        }
    });
});
