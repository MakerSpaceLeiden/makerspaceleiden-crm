
// Ensure detailed message starts with text on the first row
document.addEventListener('DOMContentLoaded', function() {
    var detailedMessageTextarea = document.getElementById('detailed_message');
    detailedMessageTextarea.addEventListener('change', function() {
        this.value = this.value.trimStart();
    });
});

// Prevent multiple rows in the motd message textarea
document.addEventListener('DOMContentLoaded', function() {
    var motdTextarea = document.getElementById('motd');
    motdTextarea.addEventListener('input', function() {
        this.value = this.value.replace(/\n/g, '');
    });
});
