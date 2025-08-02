import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
} from "chart.js";
import { Bar, Pie, Line } from "react-chartjs-2";
import {
  fetchMonitorData,
  getMockData,
  formatNumber,
  getTimeLabels,
} from "../../utils/dashboardApi.js";
import {
  exportToCSV,
  exportToJSON,
  exportChartAsPNG,
} from "../../utils/exportUtils.js";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler
);

const DashboardPage = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState("day"); // day, week, month
  const [macFilter, setMacFilter] = useState("all");
  const [sortBy, setSortBy] = useState("download");
  const [sortOrder, setSortOrder] = useState("desc");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Chart refs for export functionality
  const barChartRef = useRef(null);
  const pieChartRef = useRef(null);

  // Manual refresh function
  const handleRefresh = async () => {
    setLoading(true);
    try {
      const result = await fetchMonitorData(timeFilter, macFilter);
      setData(result.data || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to refresh dashboard data:", error);
      const mockResult = getMockData();
      setData(mockResult.data);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  };

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showExportMenu && !event.target.closest(".export-menu-container")) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showExportMenu]);
  useEffect(() => {
    console.log(
      "🔄 [DashboardPage] useEffect triggered - Data loading initiated",
      {
        timeFilter,
        macFilter,
        timestamp: new Date().toISOString(),
      }
    );

    const loadData = async () => {
      console.log("📊 [DashboardPage] Starting data load operation", {
        timeFilter,
        macFilter,
        loading: true,
      });

      setLoading(true);
      try {
        console.log("📡 [DashboardPage] Calling fetchMonitorData", {
          timeFilter,
          macFilter,
        });

        const result = await fetchMonitorData(timeFilter, macFilter);

        console.log("✅ [DashboardPage] Data received from API", {
          deviceCount: result.data ? result.data.length : 0,
          hasMetadata: !!result.metadata,
          timeFilter,
          macFilter,
        });

        setData(result.data || []);
        setLastUpdated(new Date());

        console.log("📝 [DashboardPage] State updated successfully", {
          dataLength: result.data ? result.data.length : 0,
          timeFilter,
          macFilter,
        });
      } catch (error) {
        console.error("❌ [DashboardPage] Failed to load dashboard data", {
          error: error.message,
          stack: error.stack,
          timeFilter,
          macFilter,
        });

        console.warn("🔄 [DashboardPage] Falling back to mock data");
        // Fallback to mock data
        const mockResult = getMockData();
        setData(mockResult.data);
        setLastUpdated(new Date());

        console.log("📦 [DashboardPage] Mock data set as fallback", {
          mockDataLength: mockResult.data.length,
        });
      } finally {
        setLoading(false);
        console.log("✅ [DashboardPage] Data loading completed", {
          timeFilter,
          macFilter,
          loading: false,
        });
      }
    };

    loadData();
  }, [timeFilter, macFilter]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = data;

    // Filter by MAC address
    if (macFilter !== "all") {
      filtered = filtered.filter((device) => device.mac === macFilter);
    }

    // Sort data
    filtered = [...filtered].sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      if (sortOrder === "desc") {
        return bValue - aValue;
      }
      return aValue - bValue;
    });

    return filtered;
  }, [data, macFilter, sortBy, sortOrder]);

  // Calculate totals
  const totals = useMemo(() => {
    return filteredAndSortedData.reduce(
      (acc, device) => ({
        download: acc.download + device.download,
        upload: acc.upload + device.upload,
        connections: acc.connections + device.connections,
        devices: acc.devices + 1,
      }),
      { download: 0, upload: 0, connections: 0, devices: 0 }
    );
  }, [filteredAndSortedData]);

  // Chart color palette
  const colors = [
    "#3B82F6",
    "#EF4444",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
    "#06B6D4",
    "#F97316",
    "#84CC16",
    "#EC4899",
    "#6366F1",
  ];

  // Bar chart data for download vs upload
  const barChartData = {
    labels: filteredAndSortedData.map((device) => device.ip),
    datasets: [
      {
        label: "Download (MB)",
        data: filteredAndSortedData.map((device) => device.download),
        backgroundColor: "rgba(59, 130, 246, 0.6)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 1,
      },
      {
        label: "Upload (MB)",
        data: filteredAndSortedData.map((device) => device.upload),
        backgroundColor: "rgba(239, 68, 68, 0.6)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
      },
    ],
  };

  // Pie chart data for total bandwidth usage
  const pieChartData = {
    labels: filteredAndSortedData.map(
      (device) => `${device.ip} (${device.mac.slice(-8)})`
    ),
    datasets: [
      {
        data: filteredAndSortedData.map(
          (device) => device.download + device.upload
        ),
        backgroundColor: colors.slice(0, filteredAndSortedData.length),
        borderColor: colors
          .slice(0, filteredAndSortedData.length)
          .map((color) => color.replace("0.6", "1")),
        borderWidth: 2,
      },
    ],
  };

  // Chart options
  const barChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Download vs Upload Traffic per Device",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Traffic (MB)",
        },
      },
      x: {
        title: {
          display: true,
          text: "Device IP",
        },
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "right",
      },
      title: {
        display: true,
        text: "Total Bandwidth Usage Distribution",
      },
    },
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                Loading dashboard data...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  Network Dashboard
                </h1>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  Monitor and analyze your network traffic and device usage
                  {lastUpdated && (
                    <span className="ml-2">
                      • Last updated: {lastUpdated.toLocaleTimeString()}
                    </span>
                  )}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <div className="relative export-menu-container">
                  <button
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Export
                  </button>

                  {showExportMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 rounded-md shadow-lg z-10 border border-gray-200 dark:border-gray-600">
                      <div className="py-1">
                        <button
                          onClick={() => {
                            exportToCSV(
                              filteredAndSortedData,
                              `network-data-${timeFilter}`
                            );
                            setShowExportMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                          Export as CSV
                        </button>
                        <button
                          onClick={() => {
                            exportToJSON(
                              filteredAndSortedData,
                              `network-data-${timeFilter}`
                            );
                            setShowExportMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                          Export as JSON
                        </button>
                        <button
                          onClick={() => {
                            exportChartAsPNG(
                              barChartRef,
                              `network-bar-chart-${timeFilter}`
                            );
                            setShowExportMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                          Export Bar Chart
                        </button>
                        <button
                          onClick={() => {
                            exportChartAsPNG(
                              pieChartRef,
                              `network-pie-chart-${timeFilter}`
                            );
                            setShowExportMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                          Export Pie Chart
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg
                    className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  {loading ? "Refreshing..." : "Refresh"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <svg
                  className="w-6 h-6 text-blue-600 dark:text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                  />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Download
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {totals.download.toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <svg
                  className="w-6 h-6 text-red-600 dark:text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Upload
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {totals.upload.toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <svg
                  className="w-6 h-6 text-green-600 dark:text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Connections
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {formatNumber(totals.connections)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <svg
                  className="w-6 h-6 text-purple-600 dark:text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Active Devices
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {totals.devices}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Time Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Time Range:
              </label>
              <select
                value={timeFilter}
                onChange={(e) => {
                  const newTimeFilter = e.target.value;
                  console.log(
                    "📅 [DashboardPage] Time filter dropdown changed",
                    {
                      previousValue: timeFilter,
                      newValue: newTimeFilter,
                      timestamp: new Date().toISOString(),
                    }
                  );
                  setTimeFilter(newTimeFilter);
                  console.log(
                    "📅 [DashboardPage] Time filter state update triggered",
                    {
                      newTimeFilter,
                    }
                  );
                }}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="day">Last Day</option>
                <option value="week">Last Week</option>
                <option value="month">Last Month</option>
              </select>
            </div>

            {/* MAC Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Device:
              </label>
              <select
                value={macFilter}
                onChange={(e) => {
                  const newMacFilter = e.target.value;
                  console.log(
                    "📱 [DashboardPage] MAC filter dropdown changed",
                    {
                      previousValue: macFilter,
                      newValue: newMacFilter,
                      timestamp: new Date().toISOString(),
                    }
                  );
                  setMacFilter(newMacFilter);
                  console.log(
                    "📱 [DashboardPage] MAC filter state update triggered",
                    {
                      newMacFilter,
                    }
                  );
                }}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Devices</option>
                {data.map((device) => (
                  <option key={device.mac} value={device.mac}>
                    {device.ip} ({device.mac})
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Options */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Sort by:
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="download">Download</option>
                <option value="upload">Upload</option>
                <option value="connections">Connections</option>
              </select>
              <button
                onClick={() =>
                  setSortOrder(sortOrder === "desc" ? "asc" : "desc")
                }
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {sortOrder === "desc" ? "↓" : "↑"}
              </button>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="h-96">
              <Bar
                ref={barChartRef}
                data={barChartData}
                options={barChartOptions}
              />
            </div>
          </div>

          {/* Pie Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="h-96">
              <Pie
                ref={pieChartRef}
                data={pieChartData}
                options={pieChartOptions}
              />
            </div>
          </div>
        </div>

        {/* Device Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedData.map((device, index) => (
            <div
              key={device.mac}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div
                    className="w-4 h-4 rounded-full mr-3"
                    style={{ backgroundColor: colors[index % colors.length] }}
                  ></div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {device.ip}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {device.mac}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Download:
                  </span>
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {(device.download || 0).toFixed(2)} MB
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Upload:
                  </span>
                  <span className="text-sm font-medium text-red-600 dark:text-red-400">
                    {(device.upload || 0).toFixed(2)} MB
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Connections:
                  </span>
                  <span className="text-sm font-medium text-green-600 dark:text-green-400">
                    {formatNumber(device.connections || 0)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Total Traffic:
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {((device.download || 0) + (device.upload || 0)).toFixed(2)}{" "}
                    MB
                  </span>
                </div>
              </div>

              {/* Mini Sparkline Chart */}
              <div className="mt-4 h-16">
                <Line
                  data={{
                    labels: getTimeLabels("day").slice(-6),
                    datasets: [
                      {
                        data: [
                          device.download * 0.1,
                          device.download * 0.3,
                          device.download * 0.7,
                          device.download * 0.9,
                          device.download * 0.6,
                          device.download,
                        ],
                        borderColor: colors[index % colors.length],
                        backgroundColor: colors[index % colors.length] + "20",
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      x: { display: false },
                      y: { display: false },
                    },
                    plugins: {
                      legend: { display: false },
                      title: { display: false },
                      tooltip: {
                        callbacks: {
                          title: () => "Traffic Trend",
                          label: (context) =>
                            `${context.parsed.y.toFixed(2)} MB`,
                        },
                      },
                    },
                    interaction: {
                      intersect: false,
                      mode: "index",
                    },
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredAndSortedData.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No devices found
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              No devices match the current filter criteria. Try adjusting your
              filters.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
