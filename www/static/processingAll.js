var iframe = document.getElementById("Task");
var currentState = "deleteAllChannels";

function handleIframeNavigation() {
    if (iframe.src.includes("/advanced")) {


        var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

        var form = iframeDoc.createElement('form');
        form.method = 'post';
        form.action = 'target_page.html'; // Replace with your target URL

        var input1 = iframeDoc.createElement('input');
        input1.type = 'hidden';
        input1.name = 'param1'; // Replace with your parameter name
        input1.value = 'value1'; // Replace with your parameter value

        form.appendChild(input1);
        iframeDoc.body.appendChild(form);
        form.submit();

    }
}

iframe.addEventListener("load", handleIframeNavigation);
/*
    1 - /deleteAllChannels
    2 - /processSearchForYoutubeChannels
            text YoutubeQuery = GET
            number PagesNumber = 25 
            checkbox ReplaceChannel = 1 (true) 
    3 - /processSearchForYoutubeVideos
            number PagesNumber = 25
            checkbox ReplaceCSV = 1 (true)
    4 - /concatAllChannels
    5 - /processClean
            number DeleteColumnsWithOnly = 4
            number DeleteRowsWithOnly = 2
            number OutlinerPrecise = 2.0
    6 - /processCheckForAccuracy
            number AcceptError = 50
    7 - /processTags
            number Amount = 25
    8 - /FavoriteSaveAs
            text name = GET
    REDIRECT favorites?name=GET
*/