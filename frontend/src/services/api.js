// frontend/src/services/api.js
// Central place for all API calls - keeps components clean

const API_BASE_URL = 'http://localhost:8000/api/v1';

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

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
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

// Campaign API functions (for later)
export const fetchCampaigns = async (params = {}) => {
  const searchParams = new URLSearchParams(params);
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

// Error handling helper
export const handleApiError = (error) => {
  console.error('API Error:', error);
  
  if (error.message.includes('Failed to fetch')) {
    return 'Unable to connect to the server. Please check if your backend is running.';
  }
  
  return error.message || 'An unexpected error occurred';
};