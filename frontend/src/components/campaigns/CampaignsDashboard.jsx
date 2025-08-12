// frontend/src/components/campaigns/CampaignsDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Search, Filter, Mail, RefreshCw, Plus, AlertCircle } from 'lucide-react';
import CampaignsTable from './CampaignsTable';
import CampaignsFilters from './CampaignsFilters';
import { fetchCampaigns, handleApiError, checkAPIHealth } from '../../services/api';

const CampaignsDashboard = ({ onCreateCampaign, onEditCampaign, onViewCampaign }) => {
  // State management for campaigns data
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiHealthy, setApiHealthy] = useState(true);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCampaigns, setTotalCampaigns] = useState(0);
  const [pageSize] = useState(10);
  
  // Filter state
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    is_active: null
  });
  
  // UI state
  const [showFilters, setShowFilters] = useState(false);

  // Load campaigns when component mounts or filters/page changes
  useEffect(() => {
    checkBackendHealth();
    loadCampaigns();
  }, [currentPage, filters]);
  
  const checkBackendHealth = async () => {
    try {
      const healthy = await checkAPIHealth();
      setApiHealthy(healthy);
      if (!healthy) {
        setError('Backend API is not responding. Please make sure your backend server is running on http://localhost:8000');
      }
    } catch (err) {
      setApiHealthy(false);
      setError('Unable to connect to backend API.');
    }
  };

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetchCampaigns({
        page: currentPage,
        page_size: pageSize,
        ...filters
      });
      
      setCampaigns(response.campaigns);
      setTotalPages(response.total_pages);
      setTotalCampaigns(response.total);
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to load campaigns: ${errorMessage}`);
      console.error('Error loading campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleRefresh = () => {
    loadCampaigns();
  };

  const handleCreateCampaign = () => {
    if (onCreateCampaign) {
      onCreateCampaign();
    }
  };
  
  const handleEditCampaign = (campaign) => {
    if (onEditCampaign) {
      onEditCampaign(campaign);
    }
  };
  
  const handleViewCampaign = (campaign) => {
    if (onViewCampaign) {
      onViewCampaign(campaign);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Email Campaigns</h1>
              <p className="text-gray-600 mt-1">
                Manage and track your {totalCampaigns} email campaigns
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
                className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Filter size={16} className="mr-2" />
                Filters
              </button>
              
              <button
                onClick={handleCreateCampaign}
                className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                <Plus size={16} className="mr-2" />
                Create Campaign
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Mail className="text-blue-500" size={24} />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Total Campaigns</p>
                <p className="text-2xl font-bold text-gray-900">{totalCampaigns}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">A</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">
                  {campaigns.filter(campaign => campaign.status === 'active').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">D</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Draft</p>
                <p className="text-2xl font-bold text-gray-900">
                  {campaigns.filter(campaign => campaign.status === 'draft').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-gray-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">I</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Inactive</p>
                <p className="text-2xl font-bold text-gray-900">
                  {campaigns.filter(campaign => campaign.status === 'inactive').length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mb-6">
            <CampaignsFilters 
              filters={filters}
              onFilterChange={handleFilterChange}
            />
          </div>
        )}

        {/* API Health Warning */}
        {!apiHealthy && (
          <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Backend Connection Issue</h3>
                <p className="mt-1 text-sm text-yellow-700">
                  Unable to connect to the backend API. Please ensure your FastAPI server is running on <code className="bg-yellow-100 px-1 rounded">http://localhost:8000</code>
                </p>
                <div className="mt-2">
                  <button
                    onClick={checkBackendHealth}
                    className="text-sm text-yellow-800 hover:text-yellow-900 underline"
                  >
                    Test connection again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm border">
          {error && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-red-700">{error}</p>
                  <button 
                    onClick={() => setError(null)}
                    className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          )}
          
          <CampaignsTable 
            campaigns={campaigns}
            loading={loading}
            currentPage={currentPage}
            totalPages={totalPages}
            totalCampaigns={totalCampaigns}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            onRefresh={loadCampaigns}
            onEdit={handleEditCampaign}
            onView={handleViewCampaign}
          />
        </div>
      </div>
    </div>
  );
};

export default CampaignsDashboard; 