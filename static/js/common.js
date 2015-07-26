$(document).ready(function(){   
    $(".itemcontent-content").each(function(){
        $(this).html($(this).html().replace(/((http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?)/g, "<a href=\"$1\" target=\"_blank\">$1</a>"));
    });
    $(".itemcontent-content a").each(function(){
        var url = $(this).text();
        var urlitem = $(this);
        $("<img>", {
            src: url,
            load: function() {
                urlitem.html($(this));
            },
            error: function() {
                
            }
        });
    });
});