$(document).ready(function () {
    $('#delete').on('click', function () {
        $('#access_modal').modal('show');
    });

    $('#del_enter').on('click', function () {
        key = $('#key').val();
        post_id = $('#post_id').text();
        $.ajax({
            url: '/api/post/' + post_id,
            data: {access_key: key},
            type: 'DELETE',
            complete: function (result) {
                rjson = result.responseJSON;
                if (rjson.error) {
                    alert(rjson.error);
                    return;
                }

                if (rjson.succeed) {
                    alert('delete succeed');
                    document.location.href = '/';
                }
            }
        })
    })
});