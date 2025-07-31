// frontend/src/components/leads/LeadRow.jsx
import React from 'react';
import { ExternalLink, Mail, Edit, Trash2, Phone, Linkedin } from 'lucide-react';

const LeadRow = ({ lead, onClick, onEdit, onDelete, onGenerateEmail }) => {
  
  const getStatusColor = (status) => {
    const colors = {
      'new': 'bg-gray-100 text-gray-800',
      'qualified': 'bg-green-100 text-green-800',
      'contacted': 'bg-blue-100 text-blue-800',
      'responded': 'bg-purple-100 text-purple-800',
      'converted': 'bg-emerald-100 text-emerald-800',
      'closed': 'bg-red-100 text-red-800',
      'unqualified': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-blue-600 bg-blue-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case 'linkedin':
        return <Linkedin size={14} className="text-blue-600" />;
      case 'email':
      case 'cold_email':
        return <Mail size={14} className="text-gray-600" />;
      case 'phone':
        return <Phone size={14} className="text-green-600" />;
      default:
        return <div className="w-3.5 h-3.5 bg-gray-400 rounded-full" />;
    }
  };

  return (
    <tr 
      onClick={onClick}
      className="hover:bg-gray-50 cursor-pointer transition-colors duration-150"
    >
      {/* Lead Name & Email */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-sm font-medium text-white">
                {(lead.first_name?.[0] || '') + (lead.last_name?.[0] || '')}
              </span>
            </div>
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900">
              {lead.full_name || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || 'No Name'}
            </div>
            <div className="text-sm text-gray-500">
              {lead.email}
            </div>
          </div>
        </div>
      </td>

      {/* Company & Job Title */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">
          {lead.company_name || 'No Company'}
        </div>
        <div className="text-sm text-gray-500">
          {lead.job_title || 'No Title'}
        </div>
      </td>

      {/* Contact Info */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex flex-col space-y-1">
          {lead.phone && (
            <div className="flex items-center text-sm text-gray-600">
              <Phone size={12} className="mr-1" />
              <span>{lead.phone}</span>
            </div>
          )}
          {lead.linkedin_url && (
            <div className="flex items-center">
              <a 
                href={lead.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center text-sm text-blue-600 hover:text-blue-800"
              >
                <Linkedin size={12} className="mr-1" />
                <span>LinkedIn</span>
                <ExternalLink size={10} className="ml-1" />
              </a>
            </div>
          )}
          {!lead.phone && !lead.linkedin_url && (
            <span className="text-sm text-gray-400">No contact info</span>
          )}
        </div>
      </td>

      {/* Status & Score */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex flex-col space-y-2">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(lead.status)}`}>
            {lead.status || 'unknown'}
          </span>
          <div className={`text-sm font-medium px-2 py-1 rounded-md text-center ${getScoreColor(lead.score)}`}>
            {lead.score || 0}
          </div>
        </div>
      </td>

      {/* Source */}
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          {getSourceIcon(lead.source)}
          <span className="ml-2 text-sm text-gray-900 capitalize">
            {lead.source || 'unknown'}
          </span>
        </div>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={onGenerateEmail}
            className="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
            title="Generate Email"
          >
            <Mail size={16} />
          </button>
          <button
            onClick={onEdit}
            className="text-gray-600 hover:text-gray-900 p-1 rounded hover:bg-gray-50"
            title="Edit Lead"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
            title="Delete Lead"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </td>
    </tr>
  );
};

export default LeadRow;