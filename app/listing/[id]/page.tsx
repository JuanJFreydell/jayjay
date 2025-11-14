'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { mockProperties } from '../../data/mockProperties';
import Link from 'next/link';
import { useConversation } from '../../contexts/ConversationContext';
import type { ChatMessage } from '../../contexts/ConversationContext';

export default function ListingPage() {
  const params = useParams();
  const listingId = params.id as string;
  const [inputValue, setInputValue] = useState('');
  const {
    createConversation,
    addMessage,
    getCurrentConversation,
    currentConversationId,
    setCurrentConversation,
    findConversationByPropertyId
  } = useConversation();

  const property = mockProperties.find(p => p.id === listingId);

  useEffect(() => {
    if (property && listingId) {
      // Check if there's already a conversation for this specific property ID
      const existingConversation = findConversationByPropertyId(listingId);

      if (existingConversation) {
        // Set existing conversation as current
        setCurrentConversation(existingConversation.id);
        console.log('Found existing conversation for property:', listingId);
      } else {
        // Create new conversation for this property
        console.log('Creating new conversation for property:', listingId);
        const conversationId = createConversation(
          `Property Chat - ${property.price}`,
          property.address,
          listingId
        );

        // Add initial bot message
        const initialMessage: ChatMessage = {
          id: '1',
          text: `Hi I am Jayjay, you can ask me anything about this property at ${property.address}.`,
          isUser: false,
          timestamp: new Date()
        };

        addMessage(conversationId, initialMessage);
      }
    }
  }, [property, listingId, findConversationByPropertyId, createConversation, setCurrentConversation, addMessage]);

  const sendMessage = (text: string) => {
    if (!text.trim() || !currentConversationId) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      text: text.trim(),
      isUser: true,
      timestamp: new Date()
    };

    addMessage(currentConversationId, newMessage);
    setInputValue('');
  };

  const handleQuickAction = (action: string) => {
    const actions = {
      'Book a tour': 'I would like to book a tour of this property.',
      'Get market valuation': 'Can you provide a market valuation for this property?',
      'Request a loan estimate': 'I would like to request a loan estimate for this property.',
      'Learn more about the property': 'Can you tell me more details about this property?'
    };

    sendMessage(actions[action as keyof typeof actions] || action);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  if (!property) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-black mb-4">Property Not Found</h1>
          <Link href="/" className="text-black underline hover:no-underline">
            ← Back to Search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-3 gap-8">
          {/* Left Side - Property Details (2/3) */}
          <div className="col-span-2">
            {/* Property Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-black mb-2">{property.price}</h1>
              <p className="text-xl text-gray-700 mb-4">{property.address}</p>
              <div className="flex items-center gap-6 text-lg text-gray-600">
                <span>{property.bedrooms} Bedrooms</span>
                <span>•</span>
                <span>{property.bathrooms} Bathrooms</span>
                <span>•</span>
                <span>{property.sqft.toLocaleString()} Sqft</span>
                <span>•</span>
                <span className="capitalize">{property.propertyType}</span>
              </div>
            </div>

            {/* Property Image Placeholder */}
            <div className="bg-gray-200 rounded-2xl h-96 mb-8 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🏠</div>
                <p className="text-gray-600">Property Photos Coming Soon</p>
              </div>
            </div>

            {/* Description */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-black mb-4">About This Property</h2>
              <p className="text-gray-700 leading-relaxed mb-6">
                {property.description}
              </p>

              {/* Features */}
              <h3 className="text-xl font-bold text-black mb-4">Features</h3>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-black mb-2">Bedrooms</h4>
                  <p className="text-gray-600">{property.bedrooms} spacious bedrooms</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-black mb-2">Bathrooms</h4>
                  <p className="text-gray-600">{property.bathrooms} full bathrooms</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-black mb-2">Living Space</h4>
                  <p className="text-gray-600">{property.sqft.toLocaleString()} square feet</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-black mb-2">Property Type</h4>
                  <p className="text-gray-600 capitalize">{property.propertyType}</p>
                </div>
              </div>

              {/* Neighborhood Info */}
              <h3 className="text-xl font-bold text-black mb-4">Neighborhood</h3>
              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-black mb-2">Seacliff, San Francisco</h4>
                <p className="text-gray-600 leading-relaxed">
                  Located in one of San Francisco's most exclusive neighborhoods, Seacliff offers stunning
                  ocean views, proximity to the Presidio, and easy access to Baker Beach and China Beach.
                  This prestigious area is known for its Mediterranean-style architecture and luxury homes.
                </p>
              </div>

              {/* Listing Details */}
              <div className="bg-black text-white rounded-2xl p-6 mt-6">
                <h3 className="text-xl font-bold mb-4">Listing Details</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Price:</span>
                    <span className="font-bold">{property.price}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Listed:</span>
                    <span>{new Date(property.listingDate).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Property ID:</span>
                    <span>#{property.id}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Chatbot (1/3) */}
          <div className="col-span-1">
            <div className="bg-white border border-gray-200 rounded-2xl flex flex-col sticky top-8 h-[calc(100vh-6rem)]">
              {/* Chat Header */}
              <div className="bg-black text-white p-4 rounded-t-2xl">
                <h3 className="text-lg font-bold">Ask Jayjay</h3>
                <p className="text-sm text-gray-300">Your AI Property Assistant</p>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 p-4 overflow-y-auto">
                {getCurrentConversation()?.messages.map((message) => (
                  <div key={message.id} className={`mb-4 ${message.isUser ? 'text-right' : 'text-left'}`}>
                    <div className={`inline-block p-3 rounded-lg max-w-xs ${
                      message.isUser
                        ? 'bg-black text-white'
                        : 'bg-gray-100 text-black'
                    }`}>
                      <p className="text-sm">{message.text}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                )) || []}
              </div>

              {/* Quick Action Buttons */}
              <div className="p-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <button
                    onClick={() => handleQuickAction('Book a tour')}
                    className="p-2 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Book a tour
                  </button>
                  <button
                    onClick={() => handleQuickAction('Get market valuation')}
                    className="p-2 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Get market valuation
                  </button>
                  <button
                    onClick={() => handleQuickAction('Request a loan estimate')}
                    className="p-2 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Request a loan estimate
                  </button>
                  <button
                    onClick={() => handleQuickAction('Learn more about the property')}
                    className="p-2 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Learn more about the property
                  </button>
                </div>

                {/* Chat Input */}
                <form onSubmit={handleSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Ask me anything..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-black text-sm"
                  />
                  <button
                    type="submit"
                    className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    Send
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}