import React, { useState } from 'react';
import { Download, AlertCircle } from 'lucide-react';
import { downloadAPI } from '../constants/api';

const DownloadAgentButton = () => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    setIsDownloading(true);
    setError(null);

    try {
      // Fetch the download URL from the backend using the API function
      const data = await downloadAPI.getDownloadUrl();
      
      if (!data.success || !data.data) {
        throw new Error('Invalid response from server');
      }

      const downloadUrl = data.data;
      
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = 'netpilot-agent.zip';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err) {
      console.error('Download error:', err);
      setError(err.message || 'Failed to download agent');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="text-center">
      <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
          <div className="text-left">
            <h3 className="font-semibold text-amber-800 dark:text-amber-200 mb-2">
              One-Time Setup Required
            </h3>
            <p className="text-sm text-amber-700 dark:text-amber-300">
              Before using NetPilot, you must install and configure the NetPilot Agent on your computer. 
              The agent connects to your router to enable device monitoring and control.
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={handleDownload}
        disabled={isDownloading}
        className={`inline-flex items-center px-6 py-3 text-base font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl ${
          isDownloading
            ? 'bg-gray-400 text-white cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-700 text-white'
        }`}
      >
        {isDownloading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
            Preparing Download...
          </>
        ) : (
          <>
            <Download className="w-5 h-5 mr-3" />
            Download NetPilot Agent
          </>
        )}
      </button>

      {error && (
        <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-300">
            {error}
          </p>
        </div>
      )}
    </div>
  );
};

export default DownloadAgentButton;
