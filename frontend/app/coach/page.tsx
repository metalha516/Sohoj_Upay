"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppBottomNav } from "@/components/layout/AppBottomNav";
import { ConsentGate } from "@/components/coach/ConsentGate";
import {
  ChatMessageBubble,
  MessageBubbleData,
} from "@/components/coach/ChatMessageBubble";
import { apiClient } from "@/lib/api-client";
import {
  Sparkles,
  Send,
  RotateCcw,
  Bot,
  HelpCircle,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";

const SUGGESTED_PROMPTS = [
  "Can I afford a ৳5,000 expense this month?",
  "How is my savings rate doing compared to targets?",
  "Explain my next month expense forecast",
  "How much do I need to save monthly for a ৳50,000 emergency fund in 1 year?",
];

export default function CoachPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [messages, setMessages] = useState<MessageBubbleData[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of conversation
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history on mount
  useEffect(() => {
    if (!isAuthenticated || !user?.consent_ai) {
      setLoadingHistory(false);
      return;
    }

    async function loadHistory() {
      try {
        setLoadingHistory(true);
        const historyRes = await apiClient.getChatHistory(undefined, 1);
        if (historyRes.conversations && historyRes.conversations.length > 0) {
          const latestConvo = historyRes.conversations[0];
          setActiveConversationId(latestConvo.id);
          const mapped: MessageBubbleData[] = latestConvo.messages.map((m) => {
            const toolCalls = m.tool_calls?.tools || [];
            return {
              id: m.id,
              role: m.role as "user" | "assistant",
              content: m.content,
              feedback: m.feedback,
              toolCalls: toolCalls.map((tc: any) => ({
                tool: tc.tool || "tool",
                status: "completed",
                call_index: tc.call_index,
              })),
              uiAction: m.tool_calls?.ui_action || null,
              promptVersion: m.tool_calls?.prompt_version,
              created_at: m.created_at,
            };
          });
          setMessages(mapped);
        }
      } catch (err) {
        console.warn("Failed to load chat history:", err);
      } finally {
        setLoadingHistory(false);
      }
    }

    loadHistory();
  }, [isAuthenticated, user?.consent_ai]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isStreaming) return;

    setError(null);
    setInput("");

    // Optimistically append user message
    const tempUserMsgId = `user-${Date.now()}`;
    const userMsg: MessageBubbleData = {
      id: tempUserMsgId,
      role: "user",
      content: query,
    };

    // Placeholder for streamed assistant response
    const tempAssistantMsgId = `assistant-${Date.now()}`;
    const assistantMsgPlaceholder: MessageBubbleData = {
      id: tempAssistantMsgId,
      role: "assistant",
      content: "",
      toolCalls: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsgPlaceholder]);
    setIsStreaming(true);

    try {
      await apiClient.streamChat(
        {
          message: query,
          conversation_id: activeConversationId || undefined,
          stream: true,
        },
        {
          onToolStatus: (evt) => {
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id !== tempAssistantMsgId) return msg;
                const existing = msg.toolCalls || [];
                // Check if already in list
                const idx = existing.findIndex((t) => t.tool === evt.tool);
                const updated =
                  idx >= 0
                    ? existing.map((t, i) =>
                        i === idx ? { ...t, status: evt.status } : t
                      )
                    : [...existing, { tool: evt.tool, status: evt.status, call_index: evt.call_index }];
                return { ...msg, toolCalls: updated };
              })
            );
          },
          onToken: (evt) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantMsgId
                  ? { ...msg, content: msg.content + evt.text }
                  : msg
              )
            );
          },
          onUiAction: (evt) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantMsgId
                  ? {
                      ...msg,
                      uiAction: evt.ui_action,
                      uiActionPayload: evt.payload,
                    }
                  : msg
              )
            );
          },
          onDone: (evt) => {
            if (evt.conversation_id) {
              setActiveConversationId(evt.conversation_id);
            }
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantMsgId
                  ? {
                      ...msg,
                      id: evt.message_id || msg.id,
                      content: evt.content || msg.content,
                      isStreaming: false,
                      isFallback: evt.is_fallback,
                      isGrounded: evt.is_grounded,
                    }
                  : msg
              )
            );
          },
          onError: (err) => {
            setError(err.message || "Failed to receive response from AI coach.");
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantMsgId
                  ? {
                      ...msg,
                      content:
                        msg.content ||
                        "I apologize, but I encountered an issue retrieving your financial information. Please try again or check your connection.",
                      isStreaming: false,
                      isFallback: true,
                    }
                  : msg
              )
            );
          },
        }
      );
    } catch (err: any) {
      console.error("Streaming error:", err);
      setError(err.message || "An unexpected error occurred while communicating with the AI coach.");
    } finally {
      setIsStreaming(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent" />
      </div>
    );
  }

  // If user hasn't consented to AI, show the Consent Gate
  if (user && !user.consent_ai) {
    return (
      <div className="min-h-screen bg-slate-50">
        <AppHeader />
        <main className="py-8">
          <ConsentGate />
        </main>
        <AppBottomNav />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-50 overflow-hidden">
      <AppHeader />

      {/* Main Chat Interface */}
      <main className="flex flex-1 overflow-hidden">
        <div className="mx-auto flex h-full w-full max-w-4xl flex-col bg-white border-x border-slate-200">
          {/* Coach Status Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 bg-slate-50/50">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm font-bold">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-sm font-bold text-slate-900">Sohoj Financial Coach</h1>
                  <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Active & Grounded
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Strictly grounded in your MFS transactions and pure financial calculations
                </p>
              </div>
            </div>

            {messages.length > 0 && (
              <button
                onClick={() => {
                  setMessages([]);
                  setActiveConversationId(null);
                }}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 px-2.5 py-1.5 rounded-lg hover:bg-slate-200/60 transition-colors"
                title="Start New Conversation"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">New Thread</span>
              </button>
            )}
          </div>

          {/* Conversation History / Message Scroll View */}
          <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6 space-y-4">
            {messages.length === 0 ? (
              <div className="my-auto flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 mb-4 shadow-sm">
                  <Bot className="h-8 w-8" />
                </div>
                <h2 className="text-base font-bold text-slate-900 mb-1">
                  How can I help with your finances today?
                </h2>
                <p className="max-w-md text-xs text-slate-500 mb-6">
                  Ask me about your spending patterns, emergency fund needs, or whether you can
                  safely afford an upcoming expense.
                </p>

                {/* Suggested Prompts */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl text-left">
                  {SUGGESTED_PROMPTS.map((prompt, pIdx) => (
                    <button
                      key={pIdx}
                      onClick={() => handleSendMessage(prompt)}
                      className="flex items-start gap-2.5 rounded-xl border border-slate-200 bg-slate-50/60 p-3 text-xs text-slate-700 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-900 transition-all text-left group"
                    >
                      <Lightbulb className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                      <span className="font-medium">{prompt}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatMessageBubble key={msg.id} message={msg} />
                ))}
              </>
            )}

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Prompt Input Form */}
          <div className="border-t border-slate-200 bg-white p-3 sm:p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-end gap-2"
            >
              <div className="relative flex-1">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a financial question... (e.g. Can I afford ৳5,000 this month?)"
                  rows={2}
                  disabled={isStreaming}
                  className="w-full resize-none rounded-xl border border-slate-300 p-3 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-60"
                  aria-label="Message to Sohoj Coach"
                />
              </div>

              <button
                type="submit"
                disabled={!input.trim() || isStreaming}
                className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 transition-colors shrink-0"
                aria-label="Send message"
              >
                {isStreaming ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </form>

            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span>Projections and simulations are educational and not guaranteed.</span>
              <span className="hidden sm:inline">Press Enter to send, Shift+Enter for new line</span>
            </div>
          </div>
        </div>
      </main>

      <AppBottomNav />
    </div>
  );
}
