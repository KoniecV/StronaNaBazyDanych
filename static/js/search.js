function getSuggestions() {
    var query = document.getElementById('searchInput').value;

    fetch(`/get_suggestions?query=${query}`)
        .then(response => response.json())
        .then(data => {
            displaySuggestions(data);
        });
}

function displaySuggestions(suggestions) {
    var suggestionList = document.getElementById('suggestionList');
    suggestionList.innerHTML = '';

    if (suggestions.length === 0) {
        suggestionList.innerHTML = '<li>No suggestions found</li>';
        return;
    }

    suggestions.forEach(suggestion => {
        var li = document.createElement('li');
        // Utwórz link <a> dla każdej propozycji
        var link = document.createElement('a');
        var suggestionPath = `${suggestion[0]} | ${suggestion[1]} (${suggestion[2]})`.replace(/\s+/g, ' '); // Zamień spacje na podkreślenia
        link.textContent = suggestionPath;
        link.href = `/${encodeURIComponent(suggestionPath)}`; // Przekieruj do /suggestion/[nazwa_skorki]
        li.appendChild(link);

        suggestionList.appendChild(li);
    });
}


document.addEventListener('click', function(event) {
    var suggestionList = document.getElementById('suggestionList');
    if (!event.target.closest('.search-container')) {
        suggestionList.innerHTML = '';
    }
});
