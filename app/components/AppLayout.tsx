'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useConversation } from '../contexts/ConversationContext';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const pathname = usePathname();
  const { conversations, currentConversationId, setCurrentConversation, deleteConversation } = useConversation();

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div className={`${
        isSidebarOpen ? 'w-80' : 'w-16'
      } bg-black text-white flex flex-col transition-all duration-300 ease-in-out`}>

        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          {isSidebarOpen && (
            <div>
              <h2 className="text-lg font-bold">Jayjay</h2>
              <p className="text-sm text-gray-400">AI Real Estate Assistant</p>
            </div>
          )}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            {isSidebarOpen ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>

        {/* Navigation */}
        {isSidebarOpen && (
          <div className="p-4 border-b border-gray-800">
            <Link
              href="/"
              className={`block p-3 rounded-lg transition-colors ${
                pathname === '/'
                  ? 'bg-white text-black'
                  : 'hover:bg-gray-800 text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search Properties
              </div>
            </Link>
          </div>
        )}

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {isSidebarOpen && (
            <>
              <div className="p-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Recent Conversations
                </h3>
              </div>

              <div className="px-2">
                {conversations.length === 0 ? (
                  <div className="px-4 py-8 text-center text-gray-500">
                    <p className="text-sm">No conversations yet</p>
                    <p className="text-xs mt-1">Start by searching for a property</p>
                  </div>
                ) : (
                  conversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`mb-2 p-3 rounded-lg cursor-pointer transition-colors group relative ${
                        currentConversationId === conversation.id
                          ? 'bg-white text-black'
                          : 'hover:bg-gray-800'
                      }`}
                      onClick={() => {
                        setCurrentConversation(conversation.id);
                        if (conversation.propertyId) {
                          // Navigate directly using the stored property ID
                          window.location.href = `/listing/${conversation.propertyId}`;
                        }
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium truncate">
                            {truncateTitle(conversation.title)}
                          </h4>
                          {conversation.propertyAddress && (
                            <p className="text-xs text-gray-400 mt-1 truncate">
                              {conversation.propertyAddress}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            {formatTimeAgo(conversation.lastActivity)}
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteConversation(conversation.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition-all ml-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>

        {/* Sidebar Footer */}
        {isSidebarOpen && (
          <div className="p-4 border-t border-gray-800">
            <div className="text-xs text-gray-500 text-center">
              <p>© 2024 Jayjay</p>
              <p className="mt-1">AI Real Estate Assistant</p>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}