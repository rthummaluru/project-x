// frontend/src/components/leads/LeadsDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Search, Filter, Users, RefreshCw } from 'lucide-react';
import LeadsTable from './LeadsTable';
import LeadsFilters from './LeadsFilters';
import { fetchLeads } from '../../services/api';

const LeadsDashboard = () => {
  // State management for leads data
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalLeads, setTotalLeads] = useState(0);
  const [pageSize] = useState(10); // Fixed page size for now
  
  // Stats state
  const [stats, setStats] = useState({
    total: 0,
    qualified: 0,
    new: 0,
    contacted: 0
  });
  
  // Filter state - matches your backend LeadFilter schema
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    source: '',
    company_name: '',
    min_score: 0,
    max_score: 100
  });
  
  // UI state
  const [showFilters, setShowFilters] = useState(false);

  // Load leads when component mounts or filters/page changes
  useEffect(() => {
    loadLeads();
  }, [currentPage, filters]);

  const loadLeads = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call your FastAPI backend
      const response = await fetchLeads({
        page: currentPage,
        page_size: pageSize,
        ...filters
      });
      
      setLeads(response.leads);
      setTotalPages(response.total_pages);
      setTotalLeads(response.total);
      setStats(response.stats || {
        total: response.total,
        qualified: 0,
        new: 0,
        contacted: 0
      });
      
    } catch (err) {
      setError('Failed to load leads. Please try again.');
      console.error('Error loading leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleRefresh = () => {
    loadLeads();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Leads Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Manage and track your {totalLeads} leads
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                <Filter size={16} className="mr-2" />
                Filters
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Users className="text-blue-500" size={24} />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Leads</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">Q</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Qualified</p>
                <p className="text-2xl font-bold text-gray-900">{stats.qualified}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">N</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">New</p>
                <p className="text-2xl font-bold text-gray-900">{stats.new}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">C</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Contacted</p>
                <p className="text-2xl font-bold text-gray-900">{stats.contacted}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mb-6">
            <LeadsFilters 
              filters={filters}
              onFilterChange={handleFilterChange}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm border">
          {error && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500">
              <p className="text-red-700">{error}</p>
            </div>
          )}
          
          <LeadsTable 
            leads={leads}
            loading={loading}
            currentPage={currentPage}
            totalPages={totalPages}
            totalLeads={totalLeads}
            pageSize={pageSize}
            onPageChange={handlePageChange}
          />
        </div>
      </div>
    </div>
  );
};

export default LeadsDashboard;