$(document).ready(function() 
{
    $('.add-button').click(function() 
    {
        var text = $('#text-input').val();
        if (text !== '') {
            $.ajax({
                type: 'POST',
                url: '/addChannel',
                data: {text: text},
                success: function(response) {
                    if (response.success) {
                        $('#text-input').val('');
                        var parts = text.split('/'); // Split the URL by '/'
                        $('#ChannelListContent').append(
                        "<li>"+
                            "<button type='button' class='btn-close' aria-label='Close' data-index=' "+text+" '></button> "+
                            "<a href=' "+text+" ' target='_blank'>"+parts[parts.length - 1]+"</a>"+
                            "<span style='color: grey; cursor: pointer;' onclick='window.location.reload();'> (Reload to validate)</span>"+
                        "</li>"
                        );
                    } else 
                    {
                        alert("Invalid name");
                    }
                }
            });
        }
    });

    $('.remove-button').click(function() 
    {
        var index = $(this).data('index');
        var obj = $(this);
        $.ajax({
            type: 'POST',
            url: '/removeChannel',
            data: {index: index},
            success: function(response) 
            {
                if (response.success) 
                {
                    obj.parent().remove();
                } 
                else {
                    alert("Unable to delete. Try again!");
                }
             }
        });
    });
});
