$(document).ready(function() {
    $('.add-button').click(function() {
        var text = $('#text-input').val();
        if (text !== '') {
            $.ajax({
                type: 'POST',
                url: '/addChannel',
                data: {text: text},
                success: function(response) {
                    if (response.success) {
                        $('#text-input').val('');
                        location.reload();  // Reload the page to display updated data
                    }
                }
            });
        }
    });

    $('.remove-button').click(function() {
        var index = $(this).data('index');
        $.ajax({
            type: 'POST',
            url: '/removeChannel',
            data: {index: index},
            success: function(response) {
                if (response.success) {
                    location.reload();  // Reload the page to display updated data
                }
            }
        });
    });
});
