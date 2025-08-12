// frontend/src/components/leads/EmailDraftForm.jsx
import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Sparkles, Eye, Save, RotateCcw, Copy, Loader2 } from 'lucide-react';
import { generateEmailForLead, generateCustomEmail } from '../../services/api';

const EmailDraftForm = ({ isOpen, onClose, lead, onSendEmail }) => {
  const [formData, setFormData] = useState({
    to: '',
    cc: '',
    bcc: '',
    subject: '',
    body: '',
    footer: ''
  });

  const [aiGenerationMode, setAiGenerationMode] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [errors, setErrors] = useState({});
  
  const bodyTextareaRef = useRef(null);
  const modalRef = useRef(null);

  // Auto-save to localStorage
  const AUTO_SAVE_KEY = `email_draft_${lead?.id || 'new'}`;

  useEffect(() => {
    if (isOpen && lead) {
      // Load from localStorage first
      const savedDraft = localStorage.getItem(AUTO_SAVE_KEY);
      if (savedDraft) {
        const parsedDraft = JSON.parse(savedDraft);
        setFormData(parsedDraft);
        setHasUnsavedChanges(true);
      } else {
        // Initialize with lead data
        setFormData({
          to: lead.email || '',
          cc: '',
          bcc: '',
          subject: `Follow up - ${lead.company_name || 'Your Company'}`,
          body: '',
          footer: '\n\nBest regards,\n[Your Name]\n[Your Title]\n[Your Company]'
        });
      }
    }
  }, [isOpen, lead, AUTO_SAVE_KEY]);

  // Auto-save effect
  useEffect(() => {
    if (hasUnsavedChanges && lead) {
      const timeoutId = setTimeout(() => {
        localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify(formData));
      }, 2000); // Save after 2 seconds of inactivity

      return () => clearTimeout(timeoutId);
    }
  }, [formData, hasUnsavedChanges, lead, AUTO_SAVE_KEY]);

  // Update counts when body changes
  useEffect(() => {
    const text = formData.body || '';
    setCharCount(text.length);
    setWordCount(text.trim() ? text.trim().split(/\s+/).length : 0);
  }, [formData.body]);

  // Handle form input changes
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setHasUnsavedChanges(true);
    
    // Clear field-specific errors
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (!formData.to.trim()) {
      newErrors.to = 'Recipient email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.to.trim())) {
      newErrors.to = 'Please enter a valid email address';
    }

    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    }

    if (!formData.body.trim()) {
      newErrors.body = 'Email body is required';
    }

    // Validate CC and BCC emails if provided
    if (formData.cc.trim()) {
      const ccEmails = formData.cc.split(',').map(email => email.trim());
      const invalidCC = ccEmails.find(email => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email));
      if (invalidCC) {
        newErrors.cc = 'Please enter valid email addresses separated by commas';
      }
    }

    if (formData.bcc.trim()) {
      const bccEmails = formData.bcc.split(',').map(email => email.trim());
      const invalidBCC = bccEmails.find(email => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email));
      if (invalidBCC) {
        newErrors.bcc = 'Please enter valid email addresses separated by commas';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle AI email generation
  const handleAIGeneration = async () => {
    if (!aiPrompt.trim()) {
      alert('Please enter a prompt for AI generation');
      return;
    }

    setIsGenerating(true);
    try {
      let result;
      if (aiPrompt.trim() === 'auto') {
        // Use the existing auto-generation endpoint
        result = await generateEmailForLead(lead.id);
      } else {
        // Use custom prompt
        result = await generateCustomEmail(lead.id, aiPrompt);
      }

      setGeneratedContent(result);
      
    } catch (error) {
      console.error('AI Generation Error:', error);
      alert('Failed to generate email. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Insert generated content
  const insertGeneratedContent = () => {
    if (generatedContent) {
      setFormData(prev => ({
        ...prev,
        subject: generatedContent.subject || prev.subject,
        body: generatedContent.body || generatedContent.content || prev.body
      }));
      setGeneratedContent(null);
      setAiPrompt('');
      setHasUnsavedChanges(true);
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    if (onSendEmail) {
      onSendEmail(formData);
    }

    // Clear auto-saved draft on successful send
    localStorage.removeItem(AUTO_SAVE_KEY);
    setHasUnsavedChanges(false);
    onClose();
  };

  // Handle close with unsaved changes warning
  const handleClose = () => {
    if (hasUnsavedChanges) {
      const confirmClose = window.confirm(
        'You have unsaved changes. Are you sure you want to close? Your draft will be saved locally.'
      );
      if (!confirmClose) {
        return;
      }
    }
    
    setGeneratedContent(null);
    setAiPrompt('');
    setAiGenerationMode(false);
    setShowPreview(false);
    setErrors({});
    onClose();
  };

  // Clear draft
  const clearDraft = () => {
    const confirmClear = window.confirm('Are you sure you want to clear this draft?');
    if (confirmClear) {
      setFormData({
        to: lead?.email || '',
        cc: '',
        bcc: '',
        subject: '',
        body: '',
        footer: ''
      });
      localStorage.removeItem(AUTO_SAVE_KEY);
      setHasUnsavedChanges(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(() => {
      alert('Failed to copy to clipboard');
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div 
        ref={modalRef}
        className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex"
      >
        {/* Main Email Form */}
        <div className={`flex-1 flex flex-col ${aiGenerationMode ? 'border-r border-gray-200' : ''}`}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <h2 className="text-xl font-semibold text-gray-900">Draft Email</h2>
              {lead && (
                <div className="text-sm text-gray-600">
                  to {lead.first_name} {lead.last_name} at {lead.company_name}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {hasUnsavedChanges && (
                <span className="text-sm text-orange-600">Unsaved changes</span>
              )}
              
              <button
                type="button"
                onClick={() => setAiGenerationMode(!aiGenerationMode)}
                className={`flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  aiGenerationMode
                    ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Sparkles size={16} className="mr-1.5" />
                AI Generate
              </button>
              
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center px-3 py-1.5 rounded-md text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                <Eye size={16} className="mr-1.5" />
                Preview
              </button>
              
              <button
                type="button"
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Email Form */}
          <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* To Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={formData.to}
                  onChange={(e) => handleInputChange('to', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.to ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="recipient@example.com"
                />
                {errors.to && <p className="text-red-500 text-sm mt-1">{errors.to}</p>}
              </div>

              {/* CC Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CC</label>
                <input
                  type="text"
                  value={formData.cc}
                  onChange={(e) => handleInputChange('cc', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.cc ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="cc@example.com, another@example.com"
                />
                {errors.cc && <p className="text-red-500 text-sm mt-1">{errors.cc}</p>}
              </div>

              {/* BCC Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">BCC</label>
                <input
                  type="text"
                  value={formData.bcc}
                  onChange={(e) => handleInputChange('bcc', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.bcc ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="bcc@example.com, another@example.com"
                />
                {errors.bcc && <p className="text-red-500 text-sm mt-1">{errors.bcc}</p>}
              </div>

              {/* Subject Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => handleInputChange('subject', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.subject ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter email subject"
                />
                {errors.subject && <p className="text-red-500 text-sm mt-1">{errors.subject}</p>}
              </div>

              {/* Email Body */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    Email Body <span className="text-red-500">*</span>
                  </label>
                  <div className="text-xs text-gray-500">
                    {wordCount} words, {charCount} characters
                  </div>
                </div>
                
                {showPreview ? (
                  <div className="w-full h-64 p-4 border border-gray-300 rounded-md bg-gray-50 overflow-y-auto">
                    <div className="whitespace-pre-wrap text-sm text-gray-900">
                      {formData.body || 'Email body will appear here...'}
                      {formData.footer && (
                        <div className="border-t border-gray-200 mt-4 pt-4 text-gray-600">
                          {formData.footer}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <textarea
                    ref={bodyTextareaRef}
                    value={formData.body}
                    onChange={(e) => handleInputChange('body', e.target.value)}
                    className={`w-full h-64 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                      errors.body ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Write your email message here..."
                  />
                )}
                {errors.body && <p className="text-red-500 text-sm mt-1">{errors.body}</p>}
              </div>

              {/* Footer Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Footer</label>
                <textarea
                  value={formData.footer}
                  onChange={(e) => handleInputChange('footer', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows="3"
                  placeholder="Best regards,&#10;[Your Name]&#10;[Your Company]"
                />
              </div>
            </div>

            {/* Footer Actions */}
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between bg-gray-50">
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={clearDraft}
                  className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800"
                >
                  <RotateCcw size={16} className="mr-1.5" />
                  Clear Draft
                </button>
                
                <button
                  type="button"
                  onClick={() => copyToClipboard(`${formData.subject}\n\n${formData.body}${formData.footer}`)}
                  className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800"
                >
                  <Copy size={16} className="mr-1.5" />
                  Copy All
                </button>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                
                <button
                  type="submit"
                  className="flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Send size={16} className="mr-2" />
                  Send Email
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* AI Generation Side Panel */}
        {aiGenerationMode && (
          <div className="w-96 bg-gray-50 flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">AI Email Generation</h3>
              <p className="text-sm text-gray-600">
                Describe what you want the email to accomplish, or type "auto" for automatic generation.
              </p>
            </div>
            
            <div className="flex-1 p-6 space-y-4">
              {/* AI Prompt Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Instructions
                </label>
                <textarea
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  rows="4"
                  placeholder="e.g., Write a follow-up email about our meeting yesterday, mention the product demo we discussed..."
                />
              </div>

              {/* Generate Button */}
              <button
                type="button"
                onClick={handleAIGeneration}
                disabled={isGenerating || !aiPrompt.trim()}
                className="w-full flex items-center justify-center px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={16} className="mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} className="mr-2" />
                    Generate Email
                  </>
                )}
              </button>

              {/* Generated Content Display */}
              {generatedContent && (
                <div className="mt-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-gray-900">Generated Email</h4>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(`${generatedContent.subject}\n\n${generatedContent.body || generatedContent.content}`)}
                        className="text-sm text-purple-600 hover:text-purple-800"
                      >
                        <Copy size={14} />
                      </button>
                    </div>
                    
                    {generatedContent.subject && (
                      <div className="mb-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">SUBJECT</p>
                        <p className="text-sm text-gray-900">{generatedContent.subject}</p>
                      </div>
                    )}
                    
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-1">BODY</p>
                      <div className="text-sm text-gray-900 whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {generatedContent.body || generatedContent.content}
                      </div>
                    </div>
                    
                    <button
                      type="button"
                      onClick={insertGeneratedContent}
                      className="w-full mt-4 px-3 py-2 bg-purple-100 text-purple-700 text-sm font-medium rounded-md hover:bg-purple-200"
                    >
                      Insert into Email
                    </button>
                  </div>
                </div>
              )}

              {/* Quick Prompts */}
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Prompts</h4>
                <div className="space-y-2">
                  {[
                    'auto',
                    'Write a professional introduction email',
                    'Follow up on our previous conversation',
                    'Schedule a meeting to discuss our product',
                    'Thank them for their time and interest'
                  ].map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setAiPrompt(prompt)}
                      className="w-full text-left px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-100"
                    >
                      {prompt === 'auto' ? 'Automatic generation based on lead data' : prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailDraftForm;