// Get all the tables in the document
const tables = document.querySelectorAll('table');

// Loop through each table
tables.forEach((table) => {
    // Get all the text elements inside the table
    const textElements = table.querySelectorAll('td');

    // Loop through each text element and replace underscores with spaces
    textElements.forEach((element) => {
    element.textContent = element.textContent.replace(/_/g, ' ');
    });
});