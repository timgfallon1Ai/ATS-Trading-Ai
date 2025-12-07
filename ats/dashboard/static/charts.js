function renderEquityChart(elementId, timestamps, values) {
    const ctx = document.getElementById(elementId).getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: timestamps,
            datasets: [{
                label: "Portfolio Value",
                data: values,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: false }
            }
        }
    });
}
