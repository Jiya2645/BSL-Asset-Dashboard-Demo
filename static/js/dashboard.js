let deptChartInstance = null;
let tagChartInstance = null;
let pieChartInstance = null;

function updateCharts(filtered, tagged, pending) {

    const deptCounts = {};

    filtered.forEach(asset => {

        const dept =
            asset["Deptt."] || "Unknown";

        deptCounts[dept] =
            (deptCounts[dept] || 0) + 1;
    });

    const deptCanvas =
        document.getElementById("deptChart");

    if (deptCanvas) {

        if (deptChartInstance)
            deptChartInstance.destroy();

        deptChartInstance =
            new Chart(deptCanvas, {

                type: "bar",

                data: {
                    labels: Object.keys(deptCounts),
                    datasets: [{
                        label: "Department Assets",
                        data: Object.values(deptCounts)
                    }]
                }
            });
    }

    const pieCanvas =
        document.getElementById(
            "deptPieChart"
        );

    if (pieCanvas) {

        if (pieChartInstance)
            pieChartInstance.destroy();

        pieChartInstance =
            new Chart(pieCanvas, {

                type: "pie",

                data: {
                    labels: Object.keys(deptCounts),
                    datasets: [{
                        data: Object.values(deptCounts)
                    }]
                }
            });
    }

    const tagCanvas =
        document.getElementById(
            "tagChart"
        );

    if (tagCanvas) {

        if (tagChartInstance)
            tagChartInstance.destroy();

        tagChartInstance =
            new Chart(tagCanvas, {

                type: "doughnut",

                data: {
                    labels: [
                        "Tagged",
                        "Untagged"
                    ],

                    datasets: [{
                        data: [
                            tagged,
                            pending
                        ]
                    }]
                }
            });
    }
}



function loadAssets() {

    fetch('/api/assets')

        .then(response => response.json())

        .then(data => {
            const search =
                document.getElementById('searchBox')
                    .value
                    .toLowerCase();

            const department =
                document.getElementById('departmentFilter')
                    .value;

            const location =
                document.getElementById('locationFilter')
                    .value;

            const pcMake =
                document.getElementById('pcFilter')
                    .value;

            const body =
                document.getElementById('tableBody');

            body.innerHTML = '';


            const filtered = data.filter(asset => {

                const matchesSearch =

                    !search ||

                    JSON.stringify(asset)
                        .toLowerCase()
                        .includes(search);

                const matchesDept =

                    !department ||

                    asset["Deptt."] === department;

                const matchesLocation =

                    !location ||

                    asset["Location"] === location;

                const matchesPC =

                    !pcMake ||

                    asset["PC Make"] === pcMake;

                return (

                    matchesSearch &&
                    matchesDept &&
                    matchesLocation &&
                    matchesPC

                );

            });

            const dept =
                document.getElementById(
                    "departmentFilter"
                ).value;

            fetch(
                `/api/department-summary?department=${encodeURIComponent(dept)}`
            )

                .then(response => response.json())

                .then(summary => {

                    document.getElementById(
                        "totalAssets"
                    ).innerText =
                        summary.total;

                    document.getElementById(
                        "taggedAssets"
                    ).innerText =
                        summary.tagged;

                    document.getElementById(
                        "pendingAssets"
                    ).innerText =
                        summary.pending;

                    document.getElementById(
                        "completionRate"
                    ).innerText =
                        summary.completion + "%";

                    updateCharts(filtered, summary.tagged, summary.pending);

                });

            filtered
                .slice(0, 100)
                .forEach(asset => {

                    const row =
                        document.createElement('tr');

                    row.innerHTML = `

        <td>${asset["Staff No."] || ""}</td>
        <td>${asset["Name"] || ""}</td>
        <td>${asset["Deptt."] || ""}</td>
        <td>${asset["Location"] || ""}</td>
        <td>${asset["PC Make"] || ""}</td>
        <td>${asset["HOST NAME"] || ""}</td>

    `;

                    row.style.cursor = 'pointer';

                    row.addEventListener('click', () => {

                        showAssetDetails(asset);

                    });

                    body.appendChild(row);

                });

        });

}


fetch('/api/filters')

    .then(response => response.json())

    .then(data => {

        const dept =
            document.getElementById('departmentFilter');

        const location =
            document.getElementById('locationFilter');

        const pc =
            document.getElementById('pcFilter');

        data.departments.forEach(item => {

            dept.innerHTML +=
                `<option value="${item}">${item}</option>`;

        });

        data.locations.forEach(item => {

            location.innerHTML +=
                `<option value="${item}">${item}</option>`;

        });

        data.pc_makes.forEach(item => {

            pc.innerHTML +=
                `<option value="${item}">${item}</option>`;

        });

    });



document
    .getElementById('searchBox')
    .addEventListener('keyup', loadAssets);

document
    .getElementById('departmentFilter')
    .addEventListener('change', loadAssets);

document
    .getElementById('locationFilter')
    .addEventListener('change', loadAssets);

document
    .getElementById('pcFilter')
    .addEventListener('change', loadAssets);



document
    .getElementById('exportBtn')
    .addEventListener('click', () => {

        window.location.href =
            '/export';

    });



function showAssetDetails(asset) {

    const modal =
        document.getElementById("assetModal");

    const details =
        document.getElementById("assetDetails");

    details.innerHTML = `

    <div class="asset-section">

        <h3>👤 Employee Information</h3>

        <p><strong>Name:</strong> ${asset["Name"] || "-"}</p>
        <p><strong>Staff No:</strong> ${asset["Staff No."] || "-"}</p>
        <p><strong>Department:</strong> ${asset["Deptt."] || "-"}</p>
        <p><strong>Location:</strong> ${asset["Location"] || "-"}</p>

    </div>

    <hr>

    <div class="asset-section">

        <h3>💻 PC Information</h3>

        <p><strong>PC Make:</strong> ${asset["PC Make"] || "-"}</p>
        <p><strong>PC Model:</strong> ${asset["PC Model"] || "-"}</p>
        <p><strong>Host Name:</strong> ${asset["HOST NAME"] || "-"}</p>
        <p><strong>MAC Address:</strong> ${asset["MAC ADDRESS"] || "-"}</p>
        <p><strong>RAM:</strong> ${asset["RAM"] || "-"}</p>
        <p><strong>Operating System:</strong> ${asset["OS"] || "-"}</p>

    </div>

    <hr>

    <div class="asset-section">

        <h3>🖨 Printer Information</h3>

        <p><strong>Printer Make:</strong> ${asset["Printer Make"] || "-"}</p>
        <p><strong>Printer Model:</strong> ${asset["Printer Model"] || "-"}</p>
        <p><strong>Printer Serial:</strong> ${asset["Printer Sl. No."] || "-"}</p>

    </div>

    <hr>

    <div class="asset-section">

        <h3>📠 MFD Information</h3>

        <p><strong>MFD Make:</strong> ${asset["MFD MAKE"] || "-"}</p>
        <p><strong>MFD Model:</strong> ${asset["MFD MODEL"] || "-"}</p>
        <p><strong>MFD Serial:</strong> ${asset["MFD SL. NO."] || "-"}</p>

    </div>

    <hr>

    <div class="asset-section">

        <h3>📄 Scanner Information</h3>

        <p><strong>Scanner Make:</strong> ${asset["Scanner Make"] || "-"}</p>
        <p><strong>Scanner Model:</strong> ${asset["Scanner Model"] || "-"}</p>
        <p><strong>Scanner Serial:</strong> ${asset["Scanner Sl.No."] || "-"}</p>

    </div>

    <hr>

    <div class="asset-section">

        <h3>🔋 UPS Information</h3>

        <p><strong>UPS Make:</strong> ${asset["UPS MAKE"] || "-"}</p>
        <p><strong>UPS Model:</strong> ${asset["UPS MODEL"] || "-"}</p>

    </div>

    `;

    modal.style.display = "block";
}

document
    .getElementById('closeModal')
    .addEventListener('click', () => {

        document
            .getElementById('assetModal')
            .style.display = 'none';

    });



window.onclick = function (event) {

    const modal =
        document.getElementById('assetModal');

    if (event.target === modal) {

        modal.style.display = 'none';

    }

};



loadAssets();
fetch('/api/dashboard-metrics')

    .then(response => response.json())

    .then(data => {

        document
            .getElementById(
                "locationCount"
            )
            .innerText =
            data.locations;

        document
            .getElementById(
                "pcCount"
            )
            .innerText =
            data.pc_makes;

    });
