// frontend/src/App.js
import React, { useState } from 'react';
import { Users, Mail, Menu, X } from 'lucide-react';
import LeadsDashboard from './components/leads/LeadsDashboard';
import CampaignsDashboard from './components/campaigns/CampaignsDashboard';
import CampaignWizard from './components/campaigns/CampaignWizard';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('leads'); // 'leads', 'campaigns', 'create-campaign'
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { id: 'leads', name: 'Leads', icon: Users, current: currentView === 'leads' },
    { id: 'campaigns', name: 'Campaigns', icon: Mail, current: currentView === 'campaigns' },
  ];

  const handleCreateCampaign = () => {
    setCurrentView('create-campaign');
  };

  const handleEditCampaign = (campaignId: number) => {
    console.log('Edit campaign:', campaignId);
    // TODO: Navigate to campaign edit page
  };

  const handleViewCampaign = (campaignId: number) => {
    console.log('View campaign:', campaignId);
    // TODO: Navigate to campaign view page
  };

  const handleBackToCampaigns = () => {
    setCurrentView('campaigns');
  };

  const handleCampaignCreated = () => {
    setCurrentView('campaigns');
    // You could add a success message or refresh the campaigns list here
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'leads':
        return <LeadsDashboard />;
      case 'campaigns':
        return (
          <CampaignsDashboard 
            onCreateCampaign={handleCreateCampaign}
            onEditCampaign={handleEditCampaign}
            onViewCampaign={handleViewCampaign}
          />
        );
      case 'create-campaign':
        return (
          <CampaignWizard 
            onBack={handleBackToCampaigns}
            onSuccess={handleCampaignCreated}
          />
        );
      default:
        return <LeadsDashboard />;
    }
  };

  return (
    <div className="App">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-semibold text-gray-900">Sales Automation</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={24} />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentView(item.id);
                    setSidebarOpen(false);
                  }}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full ${
                    item.current
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon
                    className={`mr-3 h-5 w-5 ${
                      item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                  />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-4">
            <h1 className="text-xl font-semibold text-gray-900">Sales Automation</h1>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full ${
                    item.current
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon
                    className={`mr-3 h-5 w-5 ${
                      item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                  />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm lg:hidden">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>
          <div className="flex-1 text-sm font-semibold leading-6 text-gray-900">
            {navigation.find(item => item.id === currentView)?.name || 'Dashboard'}
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          {renderCurrentView()}
        </main>
      </div>
    </div>
  );
}

export default App;