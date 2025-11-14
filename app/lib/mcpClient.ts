// lib/mcpClient.ts
//
// Frontend client for the FastAPI /api/chat endpoint.
// This replaces the MCP client — the FastAPI server is now the MCP gateway.

export interface ChatMessage {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
}

export interface ChatResponse {
    reply: string;
    tool: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendMCPMessage(
    userMessage: string,
    history: ChatMessage[],
    property: any
): Promise<ChatResponse> {
    // Convert history to server format:
    //   [{ role: "user"|"assistant", content: string }]
    const formattedHistory = history.map((m) => ({
        role: m.isUser ? "user" : "assistant",
        content: m.text,
    }));

    // Append latest user message
    formattedHistory.push({
        role: "user",
        content: userMessage.trim(),
    });

    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                property_id: property.id,
                messages: formattedHistory,
            }),
        });

        if (!res.ok) {
            const errorText = await res.text();
            console.error("Chat API Error:", errorText);
            return {
                reply: "Sorry — the assistant is unavailable right now.",
                tool: null,
            };
        }

        const data = await res.json();
        return {
            reply: data.reply,
            tool: data.tool,
        };
    } catch (err) {
        console.error("Chat API request failed:", err);
        return {
            reply: "Sorry — I couldn’t reach the AI assistant.",
            tool: null,
        };
    }
}
