$(document).ready(function() {
    $('#chat-form').on('submit', function(e) {
        e.preventDefault();
        const userInput = $('#user-input').val();
        $('#chat-output').append('<p>User: ' + userInput + '</p>');
        $('#user-input').val('');

        const source = new EventSource("/?user_question=" + encodeURIComponent(userInput));
        source.onmessage = function(event) {
            const chatbotMessage = event.data;
            if (chatbotMessage !== "") {
                $('#chat-output').append(chatbotMessage);
            } else {
                source.close();
            }
        };
    });
});
