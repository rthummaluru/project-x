// frontend/src/components/campaigns/CampaignsTable.jsx
import React, { useState } from 'react';
import { Mail, Edit, Trash2, Play, Pause, Eye } from 'lucide-react';
import { 
  deleteCampaign, 
  updateCampaignStatus,
  handleApiError 
} from '../../services/api';

const CampaignsTable = ({ 
  campaigns, 
  loading, 
  currentPage, 
  totalPages, 
  totalCampaigns, 
  pageSize, 
  onPageChange,
  onRefresh,
  onEdit,
  onView
}) => {
  const [actionLoading, setActionLoading] = useState({});
  const [error, setError] = useState(null);
  
  const setItemLoading = (campaignId, isLoading) => {
    setActionLoading(prev => ({
      ...prev,
      [campaignId]: isLoading
    }));
  };
  
  const isItemLoading = (campaignId) => {
    return actionLoading[campaignId] || false;
  };
  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: 'bg-yellow-100 text-yellow-800', label: 'Draft' },
      active: { color: 'bg-green-100 text-green-800', label: 'Active' },
      inactive: { color: 'bg-gray-100 text-gray-800', label: 'Inactive' }
    };
    
    const config = statusConfig[status] || statusConfig.inactive;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const handleEdit = (campaign) => {
    if (onEdit) {
      onEdit(campaign);
    } else {
      console.log('Edit campaign:', campaign.id);
    }
  };

  const handleDelete = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
      return;
    }
    
    try {
      setItemLoading(campaignId, true);
      setError(null);
      
      await deleteCampaign(campaignId);
      
      // Refresh the campaigns list
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to delete campaign: ${errorMessage}`);
      console.error('Error deleting campaign:', err);
    } finally {
      setItemLoading(campaignId, false);
    }
  };

  const handleView = (campaign) => {
    if (onView) {
      onView(campaign);
    } else {
      console.log('View campaign:', campaign.id);
    }
  };

  const handleToggleStatus = async (campaignId, currentStatus) => {
    try {
      setItemLoading(campaignId, true);
      setError(null);
      
      let newStatus;
      if (currentStatus === 'active') {
        newStatus = 'inactive';
      } else if (currentStatus === 'inactive' || currentStatus === 'draft') {
        newStatus = 'active';
      }
      
      await updateCampaignStatus(campaignId, newStatus);
      
      // Refresh the campaigns list
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to update campaign status: ${errorMessage}`);
      console.error('Error updating campaign status:', err);
    } finally {
      setItemLoading(campaignId, false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading campaigns...</p>
      </div>
    );
  }

  if (campaigns.length === 0) {
    return (
      <div className="p-8 text-center">
        <Mail className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No campaigns</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by creating your first email campaign.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
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
      
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Campaign
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Emails
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Updated
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {campaigns.map((campaign) => (
              <tr key={campaign.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {campaign.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {campaign.context?.company_name || 'No company'}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(campaign.status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div className="flex items-center space-x-2">
                    <span>{campaign.email_count || 0} total</span>
                    {campaign.sent_count > 0 && (
                      <span className="text-green-600">({campaign.sent_count} sent)</span>
                    )}
                    {campaign.failed_count > 0 && (
                      <span className="text-red-600">({campaign.failed_count} failed)</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(campaign.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(campaign.updated_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    <button
                      onClick={() => handleView(campaign)}
                      disabled={isItemLoading(campaign.id)}
                      className="text-blue-600 hover:text-blue-900 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="View campaign"
                    >
                      <Eye size={16} />
                    </button>
                    
                    <button
                      onClick={() => handleEdit(campaign)}
                      disabled={isItemLoading(campaign.id) || campaign.status === 'active'}
                      className="text-gray-600 hover:text-gray-900 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      title={campaign.status === 'active' ? 'Cannot edit active campaign' : 'Edit campaign'}
                    >
                      <Edit size={16} />
                    </button>
                    
                    {campaign.status === 'active' ? (
                      <button
                        onClick={() => handleToggleStatus(campaign.id, campaign.status)}
                        disabled={isItemLoading(campaign.id)}
                        className="text-yellow-600 hover:text-yellow-900 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Pause campaign"
                      >
                        {isItemLoading(campaign.id) ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                        ) : (
                          <Pause size={16} />
                        )}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleToggleStatus(campaign.id, campaign.status)}
                        disabled={isItemLoading(campaign.id)}
                        className="text-green-600 hover:text-green-900 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Activate campaign"
                      >
                        {isItemLoading(campaign.id) ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                        ) : (
                          <Play size={16} />
                        )}
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleDelete(campaign.id)}
                      disabled={isItemLoading(campaign.id)}
                      className="text-red-600 hover:text-red-900 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Delete campaign"
                    >
                      {isItemLoading(campaign.id) ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                      ) : (
                        <Trash2 size={16} />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span>
                {' '}to{' '}
                <span className="font-medium">
                  {Math.min(currentPage * pageSize, totalCampaigns)}
                </span>
                {' '}of{' '}
                <span className="font-medium">{totalCampaigns}</span>
                {' '}results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <button
                      key={page}
                      onClick={() => onPageChange(page)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        page === currentPage
                          ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                          : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignsTable; 