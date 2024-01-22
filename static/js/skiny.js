function getImageUrl(skinName) {
    return fetch(`/get_image_url/${encodeURIComponent(skinName)}`)
        .then(response => response.text())
        .then(imageUrl => {
            if (imageUrl === '/png/error.png') {
                // Możesz obsłużyć tutaj przypadki, gdy nie uda się pobrać adresu URL obrazka
                console.error('Error fetching image URL');
            }
            return imageUrl;
        })
        .catch(error => {
            console.error('Error fetching image URL:', error);
            return 'png/error.png'; // Domyślny obrazek w przypadku błędu
        });
}

function fetchDataAndDisplayTable() {
    fetch('/query_influxdb') // Endpoint na serwerze Flask
        .then(response => response.json())
        .then(async data => {
            // Tworzenie HTML dla tabeli
            let tableHTML = '<table class="table-products table-hover">';
            tableHTML += '<colgroup>';
            tableHTML += '<col style="width:119px">';
            tableHTML += '<col style="width:120px">';
            tableHTML += '<col style="width:100px">';
            tableHTML += '</colgroup>';
            tableHTML += '<thead>';
            tableHTML += '<tr>';
            tableHTML += '<th class="table-title" colspan="2"><a>Most Expensive Skins</span></a></th>';
            tableHTML += '<th><span class="hide-small"> Now</span></th>';
            tableHTML += '</tr>';
            tableHTML += '</thead>';
            tableHTML += '<tbody>';

            // Dodanie danych do tabeli
            for (const record of data) {
                try {
                    const imageUrl = await getImageUrl(record._measurement + " | " + record.Normal);
                    tableHTML += '<tr class="app">';
                    tableHTML += '<td class="applogo">';
                    tableHTML += '<a href="/" tabindex="-1" aria-hidden="true">';
                    tableHTML += `<img src="${imageUrl}">`;
                    tableHTML += '</a>';
                    tableHTML += '</td>';
                    tableHTML += '<td>';
                    tableHTML += '<a href="/" class="css-truncate">' + record._measurement + " " + record.Normal;
                    tableHTML += '</td>';
                    tableHTML += '<td class="text-center tabular-nums green">' + record._value + '</td>';
                    tableHTML += '</tr>';
                } catch (error) {
                    console.error('Error fetching image URL:', error);
                }
            }

            tableHTML += '</tbody>';
            tableHTML += '</table>';

            // Zaktualizuj zawartość elementu z id "table-container"
            document.getElementById('table-container').innerHTML = tableHTML;
        })
        .catch(error => console.error('Error fetching data:', error));
}

// Wywołaj funkcję przy załadowaniu strony
document.addEventListener('DOMContentLoaded', fetchDataAndDisplayTable);