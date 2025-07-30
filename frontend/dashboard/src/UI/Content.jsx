import React, { useState } from "react";
import { networkAPI } from "../constants/api";

const Content = ({ children }) => {
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleApiCheck = async () => {
    try {
      // Updated to use networkAPI helper (handles authentication automatically)
      const routerId = localStorage.getItem("routerId") || "<your_router_id>";
      const data = await networkAPI.scan(routerId);
      setResponse(JSON.stringify(data, null, 2)); // Pretty print the JSON response
      setError(null);
    } catch (err) {
      setError(`Error: ${err.message}`);
      console.log(err);

      setResponse(null);
    }
  };

  return (
    <div className="flex-1 flex content-center justify-center gap-5 p-5">
      {children}
      <button
        onClick={handleApiCheck}
        className="w-40 h-10 flex content-center justify-center bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600"
      >
        API Check
      </button>
      {response && <p className="text-green-600">{response}</p>}
      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
};

export default Content;
