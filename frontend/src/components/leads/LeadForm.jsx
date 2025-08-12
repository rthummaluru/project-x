// frontend/src/components/leads/LeadForm.jsx
import React, { useState, useEffect } from 'react';
import { X, User, Mail, Building, Phone, Linkedin, Globe, AlertCircle, Check } from 'lucide-react';
import { createLead, updateLead, handleApiError, validateLeadData } from '../../services/api';

const LeadForm = ({ isOpen, onClose, onSuccess, lead = null, mode = 'create' }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    company_name: '',
    job_title: '',
    phone: '',
    linkedin_url: '',
    source: 'other',
    source_url: '',
    score: 0,
    notes: ''
  });

  // Initialize form with lead data when in edit mode
  useEffect(() => {
    if (mode === 'edit' && lead) {
      setFormData({
        email: lead.email || '',
        first_name: lead.first_name || '',
        last_name: lead.last_name || '',
        company_name: lead.company_name || '',
        job_title: lead.job_title || '',
        phone: lead.phone || '',
        linkedin_url: lead.linkedin_url || '',
        source: lead.source || 'other',
        source_url: lead.source_url || '',
        score: lead.score || 0,
        notes: lead.notes || ''
      });
    } else {
      // Reset form for create mode
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        company_name: '',
        job_title: '',
        phone: '',
        linkedin_url: '',
        source: 'other',
        source_url: '',
        score: 0,
        notes: ''
      });
    }
    
    // Clear any existing errors when switching modes
    setError(null);
    setValidationErrors([]);
  }, [mode, lead, isOpen]);

  // Lead source options based on backend schema
  const sourceOptions = [
    { value: 'apollo', label: 'Apollo' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'website', label: 'Website' },
    { value: 'referral', label: 'Referral' },
    { value: 'cold_email', label: 'Cold Email' },
    { value: 'event', label: 'Event' },
    { value: 'other', label: 'Other' }
  ];

  const handleInputChange = (field, value) => {
    // Convert score to number to ensure proper handling
    let processedValue = value;
    if (field === 'score') {
      processedValue = value === '' ? 0 : parseInt(value) || 0;
    }
    
    setFormData(prev => ({
      ...prev,
      [field]: processedValue
    }));
    
    // Clear validation errors when user starts typing
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
    
    // Clear general error
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setValidationErrors([]);
      
      // Client-side validation
      const errors = validateLeadData(formData);
      if (errors.length > 0) {
        setValidationErrors(errors);
        return;
      }
      
      // Prepare data for API (remove empty strings, score is already a number)
      const leadData = {
        ...formData,
        // Remove empty optional fields
        first_name: formData.first_name.trim() || null,
        last_name: formData.last_name.trim() || null,
        company_name: formData.company_name.trim() || null,
        job_title: formData.job_title.trim() || null,
        phone: formData.phone.trim() || null,
        linkedin_url: formData.linkedin_url.trim() || null,
        source_url: formData.source_url.trim() || null,
        notes: formData.notes.trim() || null
      };
      
      let result;
      if (mode === 'edit' && lead) {
        result = await updateLead(lead.id, leadData);
      } else {
        result = await createLead(leadData);
      }
      
      // Success! Close form and notify parent
      onSuccess(result);
      
      // Reset form only for create mode
      if (mode === 'create') {
        setFormData({
          email: '',
          first_name: '',
          last_name: '',
          company_name: '',
          job_title: '',
          phone: '',
          linkedin_url: '',
          source: 'other',
          source_url: '',
          score: 0,
          notes: ''
        });
      }
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      const action = mode === 'edit' ? 'update' : 'create';
      setError(`Failed to ${action} lead: ${errorMessage}`);
      console.error('Error creating lead:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={handleClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              {mode === 'edit' ? 'Edit Lead' : 'Create New Lead'}
            </h3>
            <button
              onClick={handleClose}
              disabled={loading}
              className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Display */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Validation Errors */}
            {validationErrors.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Please fix the following errors:</h3>
                    <ul className="mt-2 text-sm text-red-700 list-disc pl-5">
                      {validationErrors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Contact Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="john.doe@company.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                  First Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => handleInputChange('first_name', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="John"
                    maxLength={100}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Doe"
                  maxLength={100}
                />
              </div>

              <div>
                <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Company Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Building className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="company_name"
                    value={formData.company_name}
                    onChange={(e) => handleInputChange('company_name', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Acme Corp"
                    maxLength={200}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-2">
                  Job Title
                </label>
                <input
                  type="text"
                  id="job_title"
                  value={formData.job_title}
                  onChange={(e) => handleInputChange('job_title', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Marketing Director"
                  maxLength={150}
                />
              </div>

              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Phone className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="tel"
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="linkedin_url" className="block text-sm font-medium text-gray-700 mb-2">
                  LinkedIn URL
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Linkedin className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="url"
                    id="linkedin_url"
                    value={formData.linkedin_url}
                    onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://linkedin.com/in/johndoe"
                    maxLength={500}
                  />
                </div>
              </div>
            </div>

            {/* Lead Source and Score */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-2">
                  Lead Source
                </label>
                <select
                  id="source"
                  value={formData.source}
                  onChange={(e) => handleInputChange('source', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {sourceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="source_url" className="block text-sm font-medium text-gray-700 mb-2">
                  Source URL
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Globe className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="url"
                    id="source_url"
                    value={formData.source_url}
                    onChange={(e) => handleInputChange('source_url', e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="score" className="block text-sm font-medium text-gray-700 mb-2">
                  Initial Score (0-100)
                </label>
                <input
                  type="number"
                  id="score"
                  min="0"
                  max="100"
                  value={formData.score}
                  onChange={(e) => handleInputChange('score', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                Notes
              </label>
              <textarea
                id="notes"
                rows={3}
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Any additional notes about this lead..."
              />
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {mode === 'edit' ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  <>
                    <Check size={16} className="mr-2" />
                    {mode === 'edit' ? 'Update Lead' : 'Create Lead'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LeadForm;