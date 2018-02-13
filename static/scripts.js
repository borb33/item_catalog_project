var fileAttachment = document.getElementById("FileAttachment");

if(fileAttachment != null) {
    fileAttachment.onchange = function () {
        document.getElementById("fileuploadurl").value = this.value.replace(/C:\\fakepath\\/i, '');
    };
}

$(function() {
    $('.delete-btn').click(function(event) {
        event.preventDefault();
        if(confirm('Are you sure to delete the category '+ $(this).attr('data-name') +'?')) {
            $.post($(this).attr('href'), function(data) {
                window.location.replace('/');
            });
        }
    });
});
