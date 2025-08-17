import React from "react";
import { FaDownload, FaUpload, FaShieldAlt, FaTimes } from "react-icons/fa";

const GroupRulesSummary = ({ 
  bandwidthRules, 
  contentControlRules, 
  contentCategories = [],
  isLoading = false 
}) => {
  // Helper function to get category display name
  const getCategoryDisplayName = (categoryId) => {
    const category = contentCategories.find(cat => cat.id === categoryId);
    return category ? category.name : categoryId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Helper function to get category icon
  const getCategoryIcon = (categoryId) => {
    const category = contentCategories.find(cat => cat.id === categoryId);
    if (category && category.icon) {
      return category.icon;
    }
    return FaShieldAlt;
  };

  if (isLoading) {
    return (
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-24 mb-2"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-32"></div>
        </div>
      </div>
    );
  }

  const hasBandwidthRules = bandwidthRules && (
    (bandwidthRules.download_limit_mbps !== null && bandwidthRules.download_limit_mbps !== undefined) || 
    (bandwidthRules.upload_limit_mbps !== null && bandwidthRules.upload_limit_mbps !== undefined)
  );
  
  const hasContentRules = contentControlRules && 
    contentControlRules.blocked_categories && 
    Array.isArray(contentControlRules.blocked_categories) &&
    contentControlRules.blocked_categories.length > 0;

  // If no rules, show "No rules set"
  if (!hasBandwidthRules && !hasContentRules) {
    return (
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <FaTimes className="text-sm" />
          <span className="text-sm">No rules set</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {/* Bandwidth Rules */}
      {hasBandwidthRules && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <FaDownload className="text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Bandwidth Limits
            </span>
            {!bandwidthRules.is_active && (
              <span className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                Inactive
              </span>
            )}
          </div>
          <div className="space-y-1">
            {(bandwidthRules.download_limit_mbps !== null && bandwidthRules.download_limit_mbps !== undefined) && (
              <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
                <FaDownload className="text-xs" />
                <span>Download: {bandwidthRules.download_limit_mbps} Mbps</span>
              </div>
            )}
            {(bandwidthRules.upload_limit_mbps !== null && bandwidthRules.upload_limit_mbps !== undefined) && (
              <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
                <FaUpload className="text-xs" />
                <span>Upload: {bandwidthRules.upload_limit_mbps} Mbps</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Content Control Rules */}
      {hasContentRules && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <FaShieldAlt className="text-red-600 dark:text-red-400" />
            <span className="text-sm font-medium text-red-800 dark:text-red-200">
              Blocked Content
            </span>
            {!contentControlRules.is_active && (
              <span className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                Inactive
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {contentControlRules.blocked_categories.map((categoryId) => {
              const IconComponent = getCategoryIcon(categoryId);
              return (
                <div
                  key={categoryId}
                  className="flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-800/40 text-red-700 dark:text-red-300 rounded-full text-xs"
                >
                  <IconComponent className="text-xs" />
                  <span>{getCategoryDisplayName(categoryId)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupRulesSummary;
