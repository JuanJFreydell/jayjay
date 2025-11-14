'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  propertyAddress?: string;
  propertyId?: string;
  messages: ChatMessage[];
  lastActivity: Date;
}

interface ConversationContextType {
  conversations: Conversation[];
  currentConversationId: string | null;
  createConversation: (title: string, propertyAddress?: string, propertyId?: string) => string;
  addMessage: (conversationId: string, message: ChatMessage) => void;
  setCurrentConversation: (id: string) => void;
  getCurrentConversation: () => Conversation | null;
  deleteConversation: (id: string) => void;
  findConversationByPropertyId: (propertyId: string) => Conversation | null;
}

const ConversationContext = createContext<ConversationContextType | null>(null);

export function useConversation() {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return context;
}

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('jayjay-conversations');
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations);
      // Convert date strings back to Date objects
      const conversationsWithDates = parsed.map((conv: any) => ({
        ...conv,
        lastActivity: new Date(conv.lastActivity),
        messages: conv.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }));
      setConversations(conversationsWithDates);
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('jayjay-conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  const createConversation = (title: string, propertyAddress?: string, propertyId?: string): string => {
    const id = Date.now().toString();
    const newConversation: Conversation = {
      id,
      title,
      propertyAddress,
      propertyId,
      messages: [],
      lastActivity: new Date()
    };

    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversationId(id);
    return id;
  };

  const findConversationByPropertyId = (propertyId: string): Conversation | null => {
    return conversations.find(conv => conv.propertyId === propertyId) || null;
  };

  const addMessage = (conversationId: string, message: ChatMessage) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: [...conv.messages, message],
              lastActivity: new Date()
            }
          : conv
      )
    );
  };

  const setCurrentConversation = (id: string) => {
    setCurrentConversationId(id);
  };

  const getCurrentConversation = (): Conversation | null => {
    return conversations.find(conv => conv.id === currentConversationId) || null;
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== id));
    if (currentConversationId === id) {
      setCurrentConversationId(null);
    }
  };

  return (
    <ConversationContext.Provider value={{
      conversations,
      currentConversationId,
      createConversation,
      addMessage,
      setCurrentConversation,
      getCurrentConversation,
      deleteConversation,
      findConversationByPropertyId
    }}>
      {children}
    </ConversationContext.Provider>
  );
}