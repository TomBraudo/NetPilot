// Export utilities for dashboard data
export const exportToCSV = (data, filename = "network-dashboard-data") => {
  if (!data || data.length === 0) {
    alert("No data to export");
    return;
  }

  const headers = [
    "IP Address",
    "MAC Address",
    "Download (MB)",
    "Upload (MB)",
    "Total Traffic (MB)",
    "Connections",
  ];
  const csvContent = [
    headers.join(","),
    ...data.map((device) =>
      [
        device.ip,
        device.mac,
        (device.download || 0).toFixed(2),
        (device.upload || 0).toFixed(2),
        ((device.download || 0) + (device.upload || 0)).toFixed(2),
        device.connections || 0,
      ].join(",")
    ),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const exportToJSON = (data, filename = "network-dashboard-data") => {
  if (!data || data.length === 0) {
    alert("No data to export");
    return;
  }

  const exportData = {
    timestamp: new Date().toISOString(),
    devices: data.map((device) => ({
      ip: device.ip,
      mac: device.mac,
      download_mb: device.download || 0,
      upload_mb: device.upload || 0,
      total_traffic_mb: (device.download || 0) + (device.upload || 0),
      connections: device.connections || 0,
    })),
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.json`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const exportChartAsPNG = (chartRef, filename = "network-chart") => {
  if (!chartRef || !chartRef.current) {
    alert("Chart not available for export");
    return;
  }

  const canvas = chartRef.current.canvas;
  const url = canvas.toDataURL("image/png");
  const link = document.createElement("a");
  link.download = `${filename}.png`;
  link.href = url;
  link.click();
};
