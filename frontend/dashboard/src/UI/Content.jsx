import React, { useState } from "react";

const Content = ({ children }) => {
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleApiCheck = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/router_scan");
      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status}`);
      }
      const data = await res.text();
      setResponse(data);
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
