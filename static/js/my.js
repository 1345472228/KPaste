$(document).ready(function () {
    $('#form').submit(function (e) {
        e.preventDefault()
    });
    $('input').on('dblclick', function (e) {
        e.preventDefault()
    });
    $('select.dropdown')
        .dropdown()
    ;
    $('.popup').popup();

});

$('.submit').on('click', function () {
        if (!input_check())
            return;

        var submit = $('.submit');
        submit.addClass('disabled');
        form = $('#form');
        form.addClass('loading');

        var api = '/api/post/';
        var data = new FormData();
        serialize = form.serializeArray();
        for (let i = 0; i < serialize.length; i++) {
            data.append(serialize[i].name, serialize[i].value)
        }

        var xhr = new XMLHttpRequest();
        xhr.open('post', api);
        xhr.onreadystatechange = function (ev) {
            if (xhr.readyState === 4) {
                var o = JSON.parse(xhr.response);
                if (xhr.status === 200) {

                    window.location.href = '/show/' + o.post_id;
                }
                else {
                    if (o.error) {
                        show_error(o.error);
                        submit.removeClass('disabled');
                        form.removeClass('loading');

                        return;
                    }
                    show_error()
                }
            }
        };
        xhr.send(data);
    }
);

function input_check() {
    var form = $('#form');
    if ($.trim(form.find('#rawcontent').val()).length === 0) {
        $('#code .label').show('fast');
        return false
    }
    return true
}

function show_error(content) {
    message = $('#message');
    message.show()
    message.text(content);
}
