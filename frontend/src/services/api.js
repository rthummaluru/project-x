// frontend/src/services/api.js
// Central place for all API calls - keeps components clean

const API_BASE_URL = 'http://localhost:8000/api/v1';

// API Health check
export const checkAPIHealth = async () => {
  try {
    const response = await fetch('http://localhost:8000/health');
    return response.ok;
  } catch (error) {
    return false;
  }
};

// Helper function to make authenticated requests
const apiRequest = async (endpoint, options = {}) => {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      // Add your auth token here when you implement real auth
      'Authorization': 'Bearer demo-token',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      let errorData = {};
      try {
        errorData = await response.json();
      } catch (e) {
        // Response might not be JSON
      }
      
      const errorMessage = errorData.detail || errorData.message || `HTTP error! status: ${response.status}`;
      throw new Error(errorMessage);
    }
    
    // Handle empty responses (like DELETE requests)
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    } else {
      return {}; // Return empty object for non-JSON responses
    }
  } catch (error) {
    // Re-throw fetch errors with more descriptive messages
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Unable to connect to the server. Please check if your backend is running on http://localhost:8000');
    }
    throw error;
  }
};

// Leads API functions
export const fetchLeads = async (params = {}) => {
  // Build query string from params
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value);
    }
  });
  
  const queryString = searchParams.toString();
  const endpoint = `/leads${queryString ? `?${queryString}` : ''}`;
  
  return apiRequest(endpoint);
};

export const fetchLeadById = async (leadId) => {
  return apiRequest(`/leads/${leadId}`);
};

export const updateLead = async (leadId, leadData) => {
  return apiRequest(`/leads/${leadId}`, {
    method: 'PUT',
    body: JSON.stringify(leadData),
  });
};

export const deleteLead = async (leadId) => {
  return apiRequest(`/leads/${leadId}`, {
    method: 'DELETE',
  });
};

export const generateEmailForLead = async (leadId) => {
  return apiRequest(`/leads/${leadId}/generate-email`, {
    method: 'POST',
  });
};

// Campaign API functions
export const fetchCampaigns = async (params = {}) => {
  // Build query string from params
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value);
    }
  });
  
  const queryString = searchParams.toString();
  const endpoint = `/campaigns${queryString ? `?${queryString}` : ''}`;
  
  return apiRequest(endpoint);
};

export const createCampaign = async (campaignData) => {
  return apiRequest('/campaigns/', {
    method: 'POST',
    body: JSON.stringify(campaignData),
  });
};

export const fetchCampaignById = async (campaignId) => {
  return apiRequest(`/campaigns/${campaignId}`);
};

export const updateCampaign = async (campaignId, campaignData) => {
  return apiRequest(`/campaigns/${campaignId}`, {
    method: 'PATCH',
    body: JSON.stringify(campaignData),
  });
};

export const deleteCampaign = async (campaignId) => {
  return apiRequest(`/campaigns/${campaignId}`, {
    method: 'DELETE',
  });
};

// Test campaign API connectivity
export const testCampaignAPI = async () => {
  return apiRequest('/campaigns/test');
};

// Campaign status management
export const updateCampaignStatus = async (campaignId, status) => {
  return apiRequest(`/campaigns/${campaignId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
};

export const toggleCampaignActiveStatus = async (campaignId, isActive) => {
  return apiRequest(`/campaigns/${campaignId}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: isActive }),
  });
};

// Error handling helper
export const handleApiError = (error) => {
  console.error('API Error:', error);
  
  if (error.message.includes('Failed to fetch')) {
    return 'Unable to connect to the server. Please check if your backend is running.';
  }
  
  if (error.message.includes('401') || error.message.includes('Unauthorized')) {
    return 'Authentication failed. Please check your credentials.';
  }
  
  if (error.message.includes('403') || error.message.includes('Forbidden')) {
    return 'You do not have permission to perform this action.';
  }
  
  if (error.message.includes('404') || error.message.includes('Not Found')) {
    return 'The requested resource was not found.';
  }
  
  if (error.message.includes('400') || error.message.includes('Bad Request')) {
    return 'Invalid request. Please check your input and try again.';
  }
  
  if (error.message.includes('500') || error.message.includes('Internal Server Error')) {
    return 'Server error occurred. Please try again later.';
  }
  
  return error.message || 'An unexpected error occurred';
};

// Validation helpers for campaign data
export const validateCampaignData = (campaignData) => {
  const errors = [];
  
  if (!campaignData.name || campaignData.name.trim() === '') {
    errors.push('Campaign name is required');
  }
  
  if (!campaignData.context) {
    errors.push('Campaign context is required');
  } else {
    if (!campaignData.context.company_name || campaignData.context.company_name.trim() === '') {
      errors.push('Company name is required');
    }
    if (!campaignData.context.product_description || campaignData.context.product_description.trim() === '') {
      errors.push('Product description is required');
    }
    if (!campaignData.context.problem_solved || campaignData.context.problem_solved.trim() === '') {
      errors.push('Problem solved description is required');
    }
    if (!campaignData.context.call_to_action || campaignData.context.call_to_action.trim() === '') {
      errors.push('Call to action is required');
    }
  }
  
  return errors;
};

// Format API response data for UI consumption
export const formatCampaignData = (campaign) => {
  return {
    ...campaign,
    created_at_formatted: campaign.created_at ? new Date(campaign.created_at).toLocaleDateString() : null,
    updated_at_formatted: campaign.updated_at ? new Date(campaign.updated_at).toLocaleDateString() : null,
    scheduled_start_formatted: campaign.scheduled_start ? new Date(campaign.scheduled_start).toLocaleDateString() : null,
    email_stats: {
      total: campaign.email_count || 0,
      sent: campaign.sent_count || 0,
      failed: campaign.failed_count || 0,
      pending: (campaign.email_count || 0) - (campaign.sent_count || 0) - (campaign.failed_count || 0),
      success_rate: campaign.email_count > 0 ? ((campaign.sent_count || 0) / campaign.email_count * 100).toFixed(1) : 0
    }
  };
};