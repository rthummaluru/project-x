// frontend/src/components/campaigns/CampaignWizard.jsx
import React, { useState, useMemo } from 'react';
import { ArrowLeft, ArrowRight, Check, Mail, Users, Clock, Settings, AlertCircle } from 'lucide-react';
import { createCampaign, handleApiError, validateCampaignData } from '../../services/api';

const CampaignWizard = ({ onBack, onSuccess }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    name: '',
    context: {
      company_name: '',
      product_description: '',
      problem_solved: '',
      call_to_action: '',
      tone: 'Professional'
    },
    delays: {
      delays: { "1": 0 }
    },
    max_sequence_length: 4,
    scheduled_start: null,
    lead_filter: {
      min_score: 50,
      status: '',
      source: ''
    }
  });
  
  const [validationErrors, setValidationErrors] = useState([]);

  const steps = [
    { id: 1, title: 'Campaign Basics', icon: Mail },
    { id: 2, title: 'Company Context', icon: Settings },
    { id: 3, title: 'Email Sequence', icon: Clock },
    { id: 4, title: 'Review & Create', icon: Check }
  ];

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const parts = field.split('.');
      if (parts.length === 2) {
        const [parent, child] = parts;
        setFormData(prev => ({
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value
          }
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
    
    // Clear validation errors when user starts typing
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
  };

  const handleDelayChange = (position, value) => {
    const newDelays = { ...formData.delays.delays };
    if (value === '') {
      delete newDelays[position];
    } else {
      newDelays[position] = parseInt(value) || 0;
    }
    
    setFormData(prev => ({
      ...prev,
      delays: {
        ...prev.delays,
        delays: newDelays
      }
    }));
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        return formData.name.trim() !== '';
      case 2:
        return (
          formData.context.company_name.trim() !== '' &&
          formData.context.product_description.trim() !== '' &&
          formData.context.problem_solved.trim() !== '' &&
          formData.context.call_to_action.trim() !== ''
        );
      case 3:
        return Object.keys(formData.delays.delays).length > 0;
      case 4:
        const errors = validateCampaignData(formData);
        setValidationErrors(errors);
        return errors.length === 0;
      default:
        return true;
    }
  };

  // Use useMemo to prevent infinite re-renders from validation
  const canProceed = useMemo(() => validateStep(currentStep), [currentStep, formData]);
  const canGoBack = currentStep > 1;

  const handleNext = () => {
    if (canProceed && currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    if (canGoBack) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      setValidationErrors([]);
      
      // Final validation
      const errors = validateCampaignData(formData);
      if (errors.length > 0) {
        setValidationErrors(errors);
        setError('Please fix the validation errors below.');
        return;
      }
      
      const campaignData = {
        ...formData,
        scheduled_start: formData.scheduled_start || new Date().toISOString()
      };
      
      await createCampaign(campaignData);
      onSuccess();
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(`Failed to create campaign: ${errorMessage}`);
      console.error('Error creating campaign:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Campaign Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="e.g., Q1 Sales Outreach"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                Give your campaign a descriptive name to help you identify it later.
              </p>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                id="company_name"
                value={formData.context.company_name}
                onChange={(e) => handleInputChange('context.company_name', e.target.value)}
                placeholder="Your Company Inc."
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="product_description" className="block text-sm font-medium text-gray-700 mb-2">
                What do you sell? *
              </label>
              <textarea
                id="product_description"
                value={formData.context.product_description}
                onChange={(e) => handleInputChange('context.product_description', e.target.value)}
                placeholder="Describe your product or service..."
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="problem_solved" className="block text-sm font-medium text-gray-700 mb-2">
                What problem do you solve? *
              </label>
              <textarea
                id="problem_solved"
                value={formData.context.problem_solved}
                onChange={(e) => handleInputChange('context.problem_solved', e.target.value)}
                placeholder="Describe the main problem your customers face..."
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="call_to_action" className="block text-sm font-medium text-gray-700 mb-2">
                What action do you want leads to take? *
              </label>
              <input
                type="text"
                id="call_to_action"
                value={formData.context.call_to_action}
                onChange={(e) => handleInputChange('context.call_to_action', e.target.value)}
                placeholder="e.g., Schedule a demo, Download whitepaper"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="tone" className="block text-sm font-medium text-gray-700 mb-2">
                Email Tone
              </label>
              <select
                id="tone"
                value={formData.context.tone}
                onChange={(e) => handleInputChange('context.tone', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="Professional">Professional</option>
                <option value="Casual">Casual</option>
                <option value="Direct">Direct</option>
              </select>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-8">
            {/* Email Sequence Timing */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Email Sequence Timing
              </label>
              <div className="space-y-4">
                {[1, 2, 3, 4].map((position) => (
                  <div key={position} className="flex items-center space-x-4">
                    <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                      {position}
                    </div>
                    <div className="flex-1">
                      <label className="block text-sm text-gray-700">
                        Email {position} - Send after
                      </label>
                      <div className="flex items-center space-x-2 mt-1">
                        <input
                          type="number"
                          min="0"
                          value={formData.delays.delays[position] || ''}
                          onChange={(e) => handleDelayChange(position, e.target.value)}
                          placeholder="0"
                          className="w-20 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                        <span className="text-sm text-gray-500">days</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm text-gray-500">
                Configure when each email in your sequence should be sent. Email 1 is sent immediately when the campaign starts.
              </p>
            </div>

            {/* Lead Targeting */}
            <div className="border-t pt-6">
              <label className="block text-sm font-medium text-gray-700 mb-4">
                <Users className="inline w-4 h-4 mr-2" />
                Target Leads (Optional)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="min_score" className="block text-sm text-gray-700 mb-1">
                    Minimum Score
                  </label>
                  <input
                    type="number"
                    id="min_score"
                    min="0"
                    max="100"
                    value={formData.lead_filter.min_score}
                    onChange={(e) => handleInputChange('lead_filter.min_score', parseInt(e.target.value) || 0)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="filter_status" className="block text-sm text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    id="filter_status"
                    value={formData.lead_filter.status}
                    onChange={(e) => handleInputChange('lead_filter.status', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Statuses</option>
                    <option value="new">New</option>
                    <option value="qualified">Qualified</option>
                    <option value="contacted">Contacted</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="filter_source" className="block text-sm text-gray-700 mb-1">
                    Source
                  </label>
                  <input
                    type="text"
                    id="filter_source"
                    value={formData.lead_filter.source}
                    onChange={(e) => handleInputChange('lead_filter.source', e.target.value)}
                    placeholder="e.g., LinkedIn, Website"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Target specific leads based on their score, status, or source. Leave blank to include all leads.
              </p>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Campaign Summary</h3>
              
              <div className="space-y-4">
                <div>
                  <span className="text-sm font-medium text-gray-500">Campaign Name:</span>
                  <p className="text-sm text-gray-900">{formData.name}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Company:</span>
                  <p className="text-sm text-gray-900">{formData.context.company_name}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Product:</span>
                  <p className="text-sm text-gray-900">{formData.context.product_description}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Problem Solved:</span>
                  <p className="text-sm text-gray-900">{formData.context.problem_solved}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Call to Action:</span>
                  <p className="text-sm text-gray-900">{formData.context.call_to_action}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Tone:</span>
                  <p className="text-sm text-gray-900">{formData.context.tone}</p>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Email Sequence:</span>
                  <div className="mt-1 space-y-1">
                    {Object.entries(formData.delays.delays).map(([position, delay]) => (
                      <p key={position} className="text-sm text-gray-900">
                        Email {position}: {delay === 0 ? 'Immediately' : `After ${delay} days`}
                      </p>
                    ))}
                  </div>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-500">Lead Targeting:</span>
                  <div className="mt-1 space-y-1">
                    {formData.lead_filter.min_score > 0 && (
                      <p className="text-sm text-gray-900">Minimum Score: {formData.lead_filter.min_score}</p>
                    )}
                    {formData.lead_filter.status && (
                      <p className="text-sm text-gray-900">Status: {formData.lead_filter.status}</p>
                    )}
                    {formData.lead_filter.source && (
                      <p className="text-sm text-gray-900">Source: {formData.lead_filter.source}</p>
                    )}
                    {!formData.lead_filter.min_score && !formData.lead_filter.status && !formData.lead_filter.source && (
                      <p className="text-sm text-gray-500">All leads will be targeted</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
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
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft size={16} className="mr-2" />
            Back to Campaigns
          </button>
          
          <h1 className="text-3xl font-bold text-gray-900">Create Email Campaign</h1>
          <p className="text-gray-600 mt-1">
            Set up your email campaign in a few simple steps
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    isCompleted 
                      ? 'bg-green-500 border-green-500 text-white' 
                      : isActive 
                        ? 'bg-blue-500 border-blue-500 text-white'
                        : 'bg-white border-gray-300 text-gray-400'
                  }`}>
                    {isCompleted ? (
                      <Check size={20} />
                    ) : (
                      <Icon size={20} />
                    )}
                  </div>
                  
                  <div className="ml-3">
                    <p className={`text-sm font-medium ${
                      isActive ? 'text-blue-600' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </p>
                  </div>
                  
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-0.5 mx-4 ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm border p-8">
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={handleBack}
            disabled={!canGoBack}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft size={16} className="mr-2" />
            Back
          </button>
          
          <div className="flex space-x-4">
            {currentStep < steps.length ? (
              <button
                onClick={handleNext}
                disabled={!canProceed}
                className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                Next
                <ArrowRight size={16} className="ml-2" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading || !canProceed}
                className="flex items-center px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <Check size={16} className="mr-2" />
                    Create Campaign
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignWizard; 