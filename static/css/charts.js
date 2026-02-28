new Chart(ctx, {
    type: "bar",
    data: {
        labels: labels,
        datasets: [{
            label: "Productos",
            data: values,
            backgroundColor: "rgba(0, 200, 255, 0.4)",
            borderColor: "rgb(0, 200, 255)",
            borderWidth: 2,
            borderRadius: 8
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,   // OK siempre que LIMITES la altura con CSS
        scales: {
            y: { beginAtZero: true }
        }
    }
});
