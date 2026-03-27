const API_URL = "http://127.0.0.1:5000/medicines/";

async function loadMedicines() {
    const age = document.getElementById("ageFilter").value;

    let url = API_URL + "?page=1&limit=20";

    if (age) {
        url += "&age_group=" + age;
    }

    const res = await fetch(url);
    const data = await res.json();

    const container = document.getElementById("medicineList");
    container.innerHTML = "";

    data.data.forEach(med => {
        const div = document.createElement("div");
        div.className = "card";

        div.innerHTML = `
            <h3>${med.name}</h3>
            <p>Price: ${new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR'
}).format(med.price)}</p>
            <p>Stock: ${med.stock}</p>
            <p>Category: ${med.category}</p>
            <p>Age Group: ${med.age_group}</p>
        `;

        container.appendChild(div);
    });
}