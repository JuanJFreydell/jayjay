'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { mockProperties } from '../../data/mockProperties';

import { useConversation } from '../../contexts/ConversationContext';
import type { ChatMessage } from '../../contexts/ConversationContext';

import { sendMCPMessage } from '../../lib/mcpClient';

export default function ListingPage() {
    const params = useParams();
    const listingId = params.id as string;

    const [inputValue, setInputValue] = useState('');
    const [loading, setLoading] = useState(false);

    const {
        createConversation,
        addMessage,
        getCurrentConversation,
        currentConversationId,
        setCurrentConversation,
        findConversationByPropertyId,
    } = useConversation();

    const property = mockProperties.find((p) => p.id === listingId);

    // Initialize conversation on mount
    useEffect(() => {
        if (!property) return;

        const existing = findConversationByPropertyId(listingId);

        if (existing) {
            setCurrentConversation(existing.id);
            return;
        }

        const newConvId = createConversation(
            `Property Chat - ${property.price}`,
            property.address,
            listingId
        );

        addMessage(newConvId, {
            id: 'bot-init',
            text: `Hi, I'm Jayjay — your AI assistant for ${property.address}. Ask me anything!`,
            isUser: false,
            timestamp: new Date(),
        });
    }, [property]);

    // Handle actual send
    async function sendMessage(text: string) {
        if (!text.trim() || !currentConversationId) return;

        const trimmed = text.trim();
        setInputValue('');
        setLoading(true);

        // Add user msg
        const userMsg: ChatMessage = {
            id: `${Date.now()}`,
            text: trimmed,
            isUser: true,
            timestamp: new Date(),
        };
        addMessage(currentConversationId, userMsg);

        const history = getCurrentConversation()?.messages ?? [];

        try {
            const { reply, tool } = await sendMCPMessage(trimmed, history, property);

            // Add bot reply
            addMessage(currentConversationId, {
                id: `bot-${Date.now()}`,
                text: reply,
                isUser: false,
                timestamp: new Date(),
            });

            // 🔧 Optional: React to tools
            if (tool === 'tour') {
                addMessage(currentConversationId, {
                    id: `hint-${Date.now()}`,
                    text: `To book a tour, click "Book a tour" above or provide a preferred date & time.`,
                    isUser: false,
                    timestamp: new Date(),
                });
            }

            if (tool === 'offer') {
                addMessage(currentConversationId, {
                    id: `hint-${Date.now()}`,
                    text: `You can submit an offer by providing your name, email, offer price, and contingencies.`,
                    isUser: false,
                    timestamp: new Date(),
                });
            }

            if (tool === 'valuation') {
                addMessage(currentConversationId, {
                    id: `hint-${Date.now()}`,
                    text: `To get a valuation, I can search documents or compute approximate market insights.`,
                    isUser: false,
                    timestamp: new Date(),
                });
            }

        } catch (err) {
            addMessage(currentConversationId, {
                id: `err-${Date.now()}`,
                text: "Sorry — I'm having trouble reaching the assistant right now.",
                isUser: false,
                timestamp: new Date(),
            });
        }

        setLoading(false);
    }

    const handleQuickAction = (action: string) => {
        const mapping: Record<string, string> = {
            'Book a tour': 'I would like to book a tour for this property.',
            'Get market valuation': 'Can you provide a market valuation for this property?',
            'Request a loan estimate': 'Please give me a loan estimate for this property.',
            'Learn more about the property': 'Tell me more details about this property.',
        };
        sendMessage(mapping[action] ?? action);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(inputValue);
    };

    if (!property) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-4">Property Not Found</h1>
                    <Link href="/" className="underline">
                        ← Back to Search
                    </Link>
                </div>
            </div>
        );
    }

    const messages = getCurrentConversation()?.messages ?? [];

    return (
        <div className="min-h-screen bg-white">
            <div className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-3 gap-8">

                {/* LEFT SIDE PROPERTY CONTENT */}
                {/* Preserve your original UI... */}

                {/* RIGHT SIDE CHAT */}
                <div className="col-span-1">
                    <div className="bg-white border rounded-2xl flex flex-col sticky top-8 h-[calc(100vh-6rem)]">

                        {/* Header */}
                        <div className="bg-black text-white p-4 rounded-t-2xl">
                            <h3 className="text-lg font-bold">Ask Jayjay</h3>
                            <p className="text-sm text-gray-300">AI Property Assistant</p>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 p-4 overflow-y-auto">
                            {messages.map((msg) => (
                                <div key={msg.id} className={`mb-4 ${msg.isUser ? 'text-right' : 'text-left'}`}>
                                    <div
                                        className={`inline-block p-3 rounded-lg max-w-xs ${msg.isUser ? 'bg-black text-white' : 'bg-gray-100 text-black'
                                            }`}
                                    >
                                        {msg.text}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {msg.timestamp.toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })}
                                    </p>
                                </div>
                            ))}

                            {loading && (
                                <div className="text-left mb-4 text-gray-500 text-sm">Jayjay is typing…</div>
                            )}
                        </div>

                        {/* Actions + Input */}
                        <div className="p-4 border-t">
                            <div className="grid grid-cols-2 gap-2 mb-4">
                                <button onClick={() => handleQuickAction('Book a tour')} className="p-2 bg-gray-100 rounded-lg text-xs">Book a tour</button>
                                <button onClick={() => handleQuickAction('Get market valuation')} className="p-2 bg-gray-100 rounded-lg text-xs">Get market valuation</button>
                                <button onClick={() => handleQuickAction('Request a loan estimate')} className="p-2 bg-gray-100 rounded-lg text-xs">Loan estimate</button>
                                <button onClick={() => handleQuickAction('Learn more')} className="p-2 bg-gray-100 rounded-lg text-xs">Learn more</button>
                            </div>

                            <form onSubmit={handleSubmit} className="flex gap-2">
                                <input
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder="Ask me anything..."
                                    className="flex-1 px-3 py-2 border rounded-lg focus:outline-none"
                                />
                                <button type="submit" className="bg-black text-white px-4 py-2 rounded-lg">
                                    Send
                                </button>
                            </form>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}
