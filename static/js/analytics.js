fetch('/api/department-report')

.then(response => response.json())

.then(data => {

    console.log(data);

    const bestDept =
        document.getElementById(
            "bestDept"
        );

    const worstDept =
        document.getElementById(
            "worstDept"
        );

    const totalTagged =
        document.getElementById(
            "totalTagged"
        );

    const totalAssets =
        document.getElementById(
            "totalAssets"
        );

    if(data.length === 0){
        return;
    }

    const sorted =
        [...data].sort(
            (a,b) =>
            b.completion -
            a.completion
        );

    bestDept.innerText =
        `${sorted[0].department}
         (${sorted[0].completion}%)`;

    worstDept.innerText =
        `${sorted[sorted.length-1].department}
         (${sorted[sorted.length-1].completion}%)`;

    let tagged = 0;
    let assets = 0;

    data.forEach(row => {

        tagged += row.tagged;
        assets += row.total;

    });

    totalTagged.innerText =
        tagged;

    totalAssets.innerText =
        assets;
    const ctx =
    document.getElementById(
        "completionChart"
    );

new Chart(ctx, {

    type: "bar",

    data: {

        labels:
            data.map(
                row => row.department
            ),

        datasets: [{

            label:
                "Completion %",

            data:
                data.map(
                    row => row.completion
                ),

            backgroundColor:
                "#2563eb"

        }]
    },

    options: {

        responsive: true,

        scales: {

            y: {

                beginAtZero: true,

                max: 100

            }

        }

    }

});

});