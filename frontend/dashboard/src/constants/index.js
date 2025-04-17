import { GoGoal } from "react-icons/go";
import { GrPlan } from "react-icons/gr";
import {
  IoIosStats,
  IoIosSettings,
  IoIosPerson,
  IoIosPersonAdd,
  IoIosEyeOff,
  IoIosLogIn,
  IoIosLogOut,
} from "react-icons/io";
import {
  FaChartBar,
  FaCalendarAlt,
  FaFacebookMessenger,
  FaUsersCog,
  FaListAlt,
} from "react-icons/fa";
import { FaRegQuestionCircle } from "react-icons/fa";
import { AiOutlineControl } from "react-icons/ai";
import { MdOutlineSecurity } from "react-icons/md";
import { GiRadarSweep } from "react-icons/gi";

export const staticDevices = [
  {
    type: "iPhone",
    hostname: "Dans' iphone",
    ip: "192.168.1.10",
    mac: "A4:B5:C6:D7:E8:F9",
    icon: "FaMobileAlt",
  },
  {
    type: "iPhone",
    hostname: "Dans' iphone",
    ip: "192.168.1.10",
    mac: "A4:B5:C6:D7:E8:F9",
    icon: "FaMobileAlt",
  },
  {
    type: "iPhone",
    hostname: "Dans' iphone",
    ip: "192.168.1.10",
    mac: "A4:B5:C6:D7:E8:F9",
    icon: "FaMobileAlt",
  },
  {
    type: "iPhone",
    hostname: "Dans' iphone",
    ip: "192.168.1.10",
    mac: "A4:B5:C6:D7:E8:F9",
    icon: "FaMobileAlt",
  },
  {
    type: "Laptop",
    hostname: "Ronis' Laptop",
    ip: "192.168.1.15",
    mac: "B4:C5:D6:E7:F8:G9",
    icon: "FaLaptop",
  },
  {
    type: "Smart TV",
    hostname: "Smart TV",
    ip: "192.168.1.20",
    mac: "C4:D5:E6:F7:G8:H9",
    icon: "FaTv",
  },
  {
    type: "Router",
    hostname: "Router",
    ip: "192.168.1.1",
    mac: "D4:E5:F6:G7:H8:I9",
    icon: "FaWifi",
  },
];

export const links = [
  {
    href: "/",
    icon: FaChartBar,
    text: "Dashboard",
  },
  {
    href: "/scan",
    icon: GiRadarSweep,
    text: "Scan",
    badge: {
      text: "Pro",
      color: "bg-gray-100 text-gray-800",
      darkColor: "dark:bg-gray-700 dark:text-gray-300",
    },
  },
  {
    href: "/control",
    icon: AiOutlineControl,
    text: "Control",
    badge: {
      text: "4",
      color: "bg-blue-100 text-blue-800",
      darkColor: "dark:bg-blue-900 dark:text-blue-300",
    },
  },
  {
    href: "/scantest",
    icon: MdOutlineSecurity,
    text: "Security",
  },
  {
    href: "/faqs",
    icon: FaRegQuestionCircle,
    text: "FAQs",
  },
];

export const shortcutLink = [
  {
    title: "Goals",
    icon: GoGoal,
  },
  {
    title: "Plan",
    icon: GrPlan,
  },
  {
    title: "Stats",
    icon: IoIosStats,
  },
  {
    title: "Setting",
    icon: IoIosSettings,
  },
];

// ------- ==
// chart data, later we will use this!!!

// const options = {
//   series: [44, 55, 41],
//   options: {
//     chart: {
//       type: "donut",
//       height: 350,
//     },
//     labels: ["Desktop", "Tablet", "Mobile"],
//     colors: ["#FF5733", "#33FF57", "#3357FF"],
//     legend: {
//       position: "bottom",
//       labels: {
//         colors: darkMode ? "#dddddd" : "#000000",
//       },
//     },
//     dataLabels: {
//       style: {
//         colors: ["#dddddd"],
//       },
//     },
//     responsive: [
//       {
//         breakpoint: 480,
//         options: {
//           chart: {
//             width: 200,
//           },
//           legend: {
//             position: "bottom",
//           },
//         },
//       },
//     ],
//   },
// };

// ..........
// const chartConfig = {
//   series: [
//     {
//       name: "Sales",
//       data: [50, 40, 300, 320, 500, 350, 200, 230, 500],
//     },
//   ],
//   options: {
//     chart: {
//       type: "bar",
//       height: 240,
//       toolbar: {
//         show: false,
//       },
//     },
//     title: {
//       show: false,
//     },
//     dataLabels: {
//       enabled: false,
//     },
//     colors: ["#020617"],
//     plotOptions: {
//       bar: {
//         columnWidth: "40%",
//         borderRadius: 2,
//       },
//     },
//     xaxis: {
//       axisTicks: {
//         show: false,
//       },
//       axisBorder: {
//         show: false,
//       },
//       labels: {
//         style: {
//           colors: darkMode ? "#dddddd" : "#616161",
//           fontSize: "12px",
//           fontFamily: "inherit",
//           fontWeight: 400,
//         },
//       },
//       categories: [
//         "Apr",
//         "May",
//         "Jun",
//         "Jul",
//         "Aug",
//         "Sep",
//         "Oct",
//         "Nov",
//         "Dec",
//       ],
//     },
//     yaxis: {
//       labels: {
//         style: {
//           colors: darkMode ? "#dddddd" : "#616161",
//           fontSize: "12px",
//           fontFamily: "inherit",
//           fontWeight: 400,
//         },
//       },
//     },
//     grid: {
//       show: true,
//       borderColor: "#a0a0a0",
//       strokeDashArray: 5,
//       xaxis: {
//         lines: {
//           show: true,
//         },
//       },
//       padding: {
//         top: 5,
//         right: 20,
//       },
//     },
//     fill: {
//       opacity: 0.8,
//     },
//     tooltip: {
//       theme: "dark",
//     },
//   },
// };
