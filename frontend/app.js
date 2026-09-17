let currentPage = 1;
const limit = 10;

let totalItems = 0;

let editingItemId = null;


async function getErrorMessage(response) {
    try {
        const data = await response.json();

        if (data.detail && data.detail.error) {
            return data.detail.error;
        }

        if (Array.isArray(data.detail)) {
            return data.detail
                .map(error => error.msg)
                .join(", ");
        }

        if (data.detail) {
            return data.detail;
        }

        return "Something went wrong.";

    } catch (error) {
        return "Unable to process the request.";
    }
}


async function loadItems() {

    const skip = (currentPage - 1) * limit;

    const params = new URLSearchParams();

    params.append("skip", skip);
    params.append("limit", limit);

    try {

        const response = await fetch(`/items?${params.toString()}`);

        if (!response.ok) {
            const message = await getErrorMessage(response);
            throw new Error(message);
        }

        const data = await response.json();

        totalItems = data.total;

        renderItems(data.items);

        updatePagination();

    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}


async function fetchAllItems() {

    currentPage = 1;

    document.getElementById("searchInput").value = "";
    document.getElementById("minPrice").value = "";
    document.getElementById("maxPrice").value = "";

    document.getElementById("sortBy").value = "id";
    document.getElementById("sortOrder").value = "asc";

    await loadItems();

}


async function applyFilters() {

    const search = document
        .getElementById("searchInput")
        .value
        .trim();

    const minPriceValue = document
        .getElementById("minPrice")
        .value;

    const maxPriceValue = document
        .getElementById("maxPrice")
        .value;

    const sortBy = document
        .getElementById("sortBy")
        .value;

    const sortOrder = document
        .getElementById("sortOrder")
        .value;

    if (search.length === 1) {

        alert("Search must contain at least 2 characters.");

        return;
    }

    if (
        minPriceValue !== "" &&
        maxPriceValue !== "" &&
        Number(minPriceValue) > Number(maxPriceValue)
    ) {

        alert("Minimum price cannot be greater than maximum price.");

        return;
    }


    currentPage = 1;


    const skip = 0;

    const params = new URLSearchParams();

    params.append("skip", skip);
    params.append("limit", limit);

    if (search.length >= 2) {
        params.append("q", search);
    }

    if (minPriceValue !== "") {
        params.append("min_price", minPriceValue);
    }

    if (maxPriceValue !== "") {
        params.append("max_price", maxPriceValue);
    }

    params.append("sort_by", sortBy);
    params.append("sort_order", sortOrder);


    try {

        const response = await fetch(
            `/items?${params.toString()}`
        );


        if (!response.ok) {

            const message = await getErrorMessage(response);

            throw new Error(message);
        }


        const data = await response.json();


        totalItems = data.total;


        renderItems(data.items);

        updatePagination();


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}

function renderItems(items) {

    const tableBody = document.getElementById("itemsTable");

    tableBody.innerHTML = "";

    if (items.length === 0) {

        const row = document.createElement("tr");

        const cell = document.createElement("td");

        cell.colSpan = 4;

        cell.textContent = "No items found.";

        row.appendChild(cell);

        tableBody.appendChild(row);

        return;
    }


    items.forEach(item => {

        const row = document.createElement("tr");

        const idCell = document.createElement("td");

        idCell.textContent = item.id;

        const nameCell = document.createElement("td");

        nameCell.textContent = item.name;

        const priceCell = document.createElement("td");

        priceCell.textContent = formatPrice(item.price);

        const actionCell = document.createElement("td");

        const editButton = document.createElement("button");

        editButton.textContent = "Edit";

        editButton.type = "button";

        editButton.onclick = function () {
            editItem(item.id);
        };

        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";

        deleteButton.type = "button";

        deleteButton.classList.add("delete-btn");

        deleteButton.onclick = function () {
            deleteItem(item.id);
        };


        actionCell.appendChild(editButton);

        actionCell.appendChild(deleteButton);

        row.appendChild(idCell);

        row.appendChild(nameCell);

        row.appendChild(priceCell);

        row.appendChild(actionCell);

        tableBody.appendChild(row);

    });
}

function formatPrice(price) {

    return new Intl.NumberFormat("vi-VN").format(price);
}

function updatePagination() {

    const pageInfo = document.getElementById("pageInfo");


    const totalPages = Math.ceil(totalItems / limit);


    if (totalPages === 0) {

        pageInfo.textContent = "Page 0";

        return;
    }


    pageInfo.textContent =
        `Page ${currentPage} of ${totalPages}`;
}

async function previousPage() {

    if (currentPage <= 1) {
        return;
    }


    currentPage--;

    await loadCurrentView();
}

async function nextPage() {

    const totalPages = Math.ceil(totalItems / limit);


    if (currentPage >= totalPages) {
        return;
    }


    currentPage++;

    await loadCurrentView();
}

async function loadCurrentView() {

    const search = document
        .getElementById("searchInput")
        .value
        .trim();

    const minPrice = document
        .getElementById("minPrice")
        .value;

    const maxPrice = document
        .getElementById("maxPrice")
        .value;

    const sortBy = document
        .getElementById("sortBy")
        .value;

    const sortOrder = document
        .getElementById("sortOrder")
        .value;


    const skip = (currentPage - 1) * limit;


    const params = new URLSearchParams();

    params.append("skip", skip);

    params.append("limit", limit);


    if (search.length >= 2) {
        params.append("q", search);
    }


    if (minPrice !== "") {
        params.append("min_price", minPrice);
    }


    if (maxPrice !== "") {
        params.append("max_price", maxPrice);
    }


    params.append("sort_by", sortBy);

    params.append("sort_order", sortOrder);


    try {

        const response = await fetch(
            `/items?${params.toString()}`
        );


        if (!response.ok) {

            const message = await getErrorMessage(response);

            throw new Error(message);
        }


        const data = await response.json();


        totalItems = data.total;


        renderItems(data.items);

        updatePagination();


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}

document
    .getElementById("itemForm")
    .addEventListener("submit", async function (event) {

        event.preventDefault();


        const nameInput =
            document.getElementById("itemName");

        const priceInput =
            document.getElementById("itemPrice");


        const name = nameInput.value.trim();

        const price = Number(priceInput.value);

        if (!name) {

            alert("Please enter an item name.");

            return;
        }

        if (price < 0 || Number.isNaN(price)) {

            alert("Price must be greater than or equal to 0.");

            return;
        }

        if (editingItemId !== null) {

            await updateItem(
                editingItemId,
                name,
                price
            );

            return;
        }

        try {

            const response = await fetch("/items", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    price: price
                })

            });


            if (!response.ok) {

                const message =
                    await getErrorMessage(response);

                throw new Error(message);
            }


            const newItem = await response.json();


            alert(
                `Item "${newItem.name}" added successfully.`
            );

            document.getElementById("itemForm").reset();

            currentPage = 1;

            await loadItems();


        } catch (error) {

            console.error(error);

            showError(error.message);
        }

    });


async function editItem(itemId) {

    try {

        const response =
            await fetch(`/items/${itemId}`);


        if (!response.ok) {

            const message =
                await getErrorMessage(response);

            throw new Error(message);
        }


        const item = await response.json();

        document.getElementById("itemName").value =
            item.name;

        document.getElementById("itemPrice").value =
            item.price;

        editingItemId = item.id;

        document.getElementById("formTitle").textContent =
            "Edit Item";

        document.getElementById("submitBtn").textContent =
            "Update Item";

        document
            .getElementById("cancelBtn")
            .classList.remove("hidden");

        document
            .getElementById("itemForm")
            .scrollIntoView({
                behavior: "smooth",
                block: "center"
            });


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}

async function updateItem(itemId, name, price) {

    try {

        const response = await fetch(
            `/items/${itemId}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    price: price
                })
            }
        );


        if (!response.ok) {

            const message =
                await getErrorMessage(response);

            throw new Error(message);
        }


        const updatedItem =
            await response.json();


        alert(
            `Item "${updatedItem.name}" updated successfully.`
        );


        cancelEdit();


        await loadCurrentView();


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}

function cancelEdit() {

    editingItemId = null;


    document
        .getElementById("itemForm")
        .reset();


    document.getElementById("formTitle").textContent =
        "Add Item";


    document.getElementById("submitBtn").textContent =
        "Add Item";


    document
        .getElementById("cancelBtn")
        .classList.add("hidden");
}

async function deleteItem(itemId) {

    const confirmed = confirm(
        "Are you sure you want to delete this item?"
    );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(`/items/${itemId}`, {
                method: "DELETE"
            });


        if (!response.ok) {

            const message =
                await getErrorMessage(response);

            throw new Error(message);
        }


        alert("Item deleted successfully.");

        const remainingItemsOnPage =
            totalItems - 1;


        const totalPagesAfterDelete =
            Math.ceil(remainingItemsOnPage / limit);


        if (
            currentPage > totalPagesAfterDelete &&
            currentPage > 1
        ) {
            currentPage--;
        }


        await loadCurrentView();


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}

async function predictHousePrice() {

    const area =
        Number(document.getElementById("area").value);

    const bedrooms =
        Number(document.getElementById("bedrooms").value);

    const distance =
        Number(document.getElementById("distance").value);

    if (!area || area <= 0) {

        alert("Area must be greater than 0.");

        return;
    }


    if (
        Number.isNaN(bedrooms) ||
        bedrooms < 0
    ) {

        alert("Bedrooms must be greater than or equal to 0.");

        return;
    }


    if (
        Number.isNaN(distance) ||
        distance < 0
    ) {

        alert(
            "Distance must be greater than or equal to 0."
        );

        return;
    }


    try {

        const response = await fetch(
            "/predict/house-price",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    area_sqm: area,

                    bedrooms: bedrooms,

                    distance_to_center_km: distance

                })
            }
        );


        if (!response.ok) {

            const message =
                await getErrorMessage(response);

            throw new Error(message);
        }


        const data = await response.json();

        document.getElementById(
            "predictionResult"
        ).textContent =
            `${formatPrice(data.predicted_price)} ${data.currency}`;


    } catch (error) {

        console.error(error);

        showError(error.message);
    }
}


function showError(message) {

    alert(`Error: ${message}`);
}