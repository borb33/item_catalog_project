var fileAttachment = document.getElementById("FileAttachment");

if(fileAttachment != null) {
    fileAttachment.onchange = function () {
        document.getElementById("fileuploadurl").value = this.value.replace(/C:\\fakepath\\/i, '');
    };
}

$(function() {
    $('.delete-btn').click(function(event) {
        event.preventDefault();
        var item = $(this).attr('data-item');
        var name = $(this).attr('data-name');
        var location = item !== undefined ? '/catalog/'+name : '/';
        var itemMessage = item !== undefined ? 'the item '+item+' for ' : '';

        if(confirm('Are you sure to delete '+itemMessage+'the category '+name+'?')) {
            $.ajax({
                type: 'POST',
                url: $(this).attr('href'),
                success: function(data) {
                    window.location.replace(location);
                }
            });
        }
    });
});
