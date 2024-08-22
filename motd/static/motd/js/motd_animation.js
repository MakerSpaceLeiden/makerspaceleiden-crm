document.addEventListener('DOMContentLoaded', function() {
    var motdText = document.getElementById('motd-text');
    if (motdText) {
        var motd= motdText.querySelectorAll('.motd-message');

        var totalMessageLength = 0;

        motd.forEach(function(message) {
            var messageLength = message.textContent.length;
            totalMessageLength += messageLength; // Add current message length to total
        });

        // Adjust the animation duration based on total message length
        var animationDuration = 15 + (totalMessageLength * 0.15); // Adjust the multiplier as needed

        // Limit the animation duration to a maximum of 45 seconds
        animationDuration = Math.min(animationDuration, 300);

        motdText.style.animationDuration = animationDuration + 's';
    }
});
