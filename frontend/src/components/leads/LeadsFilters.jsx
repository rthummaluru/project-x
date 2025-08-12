// frontend/src/components/leads/LeadsFilters.jsx
import React from 'react';
import { Search, X } from 'lucide-react';

const LeadsFilters = ({ filters, onFilterChange }) => {
  
  const handleInputChange = (field, value) => {
    const newFilters = {
      ...filters,
      [field]: value
    };
    onFilterChange(newFilters);
  };

  const handleScoreRangeChange = (type, value) => {
    const newFilters = {
      ...filters,
      [type]: parseInt(value)
    };
    onFilterChange(newFilters);
  };

  const clearAllFilters = () => {
    const clearedFilters = {
      search: '',
      status: '',
      source: '',
      company_name: '',
      min_score: 0,
      max_score: 100
    };
    onFilterChange(clearedFilters);
  };

  const hasActiveFilters = () => {
    return (
      filters.search ||
      filters.status ||
      filters.source ||
      filters.company_name ||
      filters.min_score > 0 ||
      filters.max_score < 100
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filter Leads</h3>
        {hasActiveFilters() && (
          <button
            onClick={clearAllFilters}
            className="flex items-center text-sm text-gray-500 hover:text-red-600"
          >
            <X size={16} className="mr-1" />
            Clear All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search
          </label>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => handleInputChange('search', e.target.value)}
              placeholder="Name, email, or company..."
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => handleInputChange('status', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="qualified">Qualified</option>
            <option value="contacted">Contacted</option>
            <option value="responded">Responded</option>
            <option value="converted">Converted</option>
            <option value="closed">Closed</option>
            <option value="unqualified">Unqualified</option>
          </select>
        </div>

        {/* Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Source
          </label>
          <select
            value={filters.source}
            onChange={(e) => handleInputChange('source', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Sources</option>
            <option value="apollo">Apollo</option>
            <option value="linkedin">LinkedIn</option>
            <option value="website">Website</option>
            <option value="referral">Referral</option>
            <option value="cold_email">Cold Email</option>
            <option value="event">Event</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Company Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company
          </label>
          <input
            type="text"
            value={filters.company_name}
            onChange={(e) => handleInputChange('company_name', e.target.value)}
            placeholder="Filter by company..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Score Range */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Lead Score Range: {filters.min_score} - {filters.max_score}
          </label>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">Min Score</label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.min_score}
                onChange={(e) => handleScoreRangeChange('min_score', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0</span>
                <span>100</span>
              </div>
            </div>
            
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">Max Score</label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.max_score}
                onChange={(e) => handleScoreRangeChange('max_score', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0</span>
                <span>100</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters() && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            {filters.search && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Search: "{filters.search}"
                <button
                  onClick={() => handleInputChange('search', '')}
                  className="ml-1 hover:text-blue-600"
                >
                  <X size={12} />
                </button>
              </span>
            )}
            
            {filters.status && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Status: {filters.status}
                <button
                  onClick={() => handleInputChange('status', '')}
                  className="ml-1 hover:text-green-600"
                >
                  <X size={12} />
                </button>
              </span>
            )}
            
            {filters.source && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Source: {filters.source}
                <button
                  onClick={() => handleInputChange('source', '')}
                  className="ml-1 hover:text-purple-600"
                >
                  <X size={12} />
                </button>
              </span>
            )}
            
            {(filters.min_score > 0 || filters.max_score < 100) && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                Score: {filters.min_score}-{filters.max_score}
                <button
                  onClick={() => {
                    handleScoreRangeChange('min_score', 0);
                    handleScoreRangeChange('max_score', 100);
                  }}
                  className="ml-1 hover:text-orange-600"
                >
                  <X size={12} />
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LeadsFilters;