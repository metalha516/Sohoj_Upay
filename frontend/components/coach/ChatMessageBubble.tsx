"use client";

import React, { useState } from "react";
import { SafeMarkdown } from "./SafeMarkdown";
import { UiActionButton } from "./UiActionButton";
import { ToolStatusChip } from "./ToolStatusChip";
import { apiClient } from "@/lib/api-client";
import {
  Sparkles,
  User as UserIcon,
  ThumbsUp,
  ThumbsDown,
  Check,
  AlertCircle,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";

export interface MessageBubbleData {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: Array<{ tool: string; status: "running" | "completed"; call_index?: number }>;
  uiAction?: string | null;
  uiActionPayload?: Record<string, any> | null;
  isStreaming?: boolean;
  isFallback?: boolean;
  isGrounded?: boolean;
  promptVersion?: string;
  feedback?: number | null;
  created_at?: string;
}

interface ChatMessageBubbleProps {
  message: MessageBubbleData;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const [feedback, setFeedback] = useState<number | null>(message.feedback ?? null);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const isUser = message.role === "user";

  const handleFeedback = async (rating: number) => {
    if (feedback !== null || submittingFeedback || !message.id) return;
    try {
      setSubmittingFeedback(true);
      setFeedback(rating);
      await apiClient.postChatFeedback(message.id, { feedback: rating });
    } catch (e) {
      console.error("Failed to submit feedback", e);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 my-4 animate-fade-in-up">
        <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl bg-navy-900 px-4 py-3 text-white shadow-md border border-navy-800">
          <p className="text-sm whitespace-pre-wrap leading-relaxed font-medium">{message.content}</p>
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-100 text-navy-900 text-xs font-black border border-navy-200">
          <UserIcon className="h-4 w-4" />
        </div>
      </div>
    );
  }

  // Assistant Bubble
  return (
    <div className="flex justify-start gap-3 my-4 animate-fade-in-up">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-navy-900 text-upay-yellow shadow-sm font-bold text-xs mt-1 border border-navy-800">
        <Sparkles className="h-4 w-4" />
      </div>

      <div className="max-w-[90%] sm:max-w-[80%] rounded-2xl border border-slate-200/80 border-l-2 border-l-upay-500/40 bg-white p-4 shadow-sm space-y-3">
        {/* Tool Execution Chips */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pb-2 border-b border-slate-100">
            {message.toolCalls.map((tc, idx) => (
              <ToolStatusChip
                key={`${tc.tool}-${idx}`}
                tool={tc.tool}
                status={tc.status}
                callIndex={tc.call_index}
              />
            ))}
          </div>
        )}

        {/* Fallback Notice */}
        {message.isFallback && (
          <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5 text-xs text-amber-800 border border-amber-200">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>AI Provider degraded. Deterministic rule-grounded response provided.</span>
          </div>
        )}

        {/* Message Content */}
        <div>
          <SafeMarkdown content={message.content} />
          {message.isStreaming && (
            <span className="inline-block h-3.5 w-1.5 bg-upay-yellow animate-pulse ml-1 align-middle" />
          )}
        </div>

        {/* UI Action Button */}
        {message.uiAction && (
          <UiActionButton action={message.uiAction} payload={message.uiActionPayload} />
        )}

        {/* Trust Badges & Footers */}
        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-navy-950 bg-upay-yellow/20 px-2 py-0.5 rounded-full font-bold border border-upay-yellow/40">
              <ShieldCheck className="h-3 w-3 text-navy-900" />
              Grounded AI
            </span>
            {message.promptVersion && (
              <span className="text-slate-400 font-mono">v{message.promptVersion}</span>
            )}
          </div>

          {/* Feedback Buttons */}
          {!message.isStreaming && message.id && (
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 mr-1">Was this helpful?</span>
              <button
                onClick={() => handleFeedback(1)}
                disabled={feedback !== null || submittingFeedback}
                className={`p-1 rounded hover:bg-slate-100 transition-colors ${
                  feedback === 1 ? "text-navy-900 font-bold bg-upay-yellow/30" : "text-slate-400"
                }`}
                title="Helpful"
                aria-label="Thumbs up"
              >
                <ThumbsUp className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleFeedback(-1)}
                disabled={feedback !== null || submittingFeedback}
                className={`p-1 rounded hover:bg-slate-100 transition-colors ${
                  feedback === -1 ? "text-rose-600 font-bold bg-rose-50" : "text-slate-400"
                }`}
                title="Not helpful"
                aria-label="Thumbs down"
              >
                <ThumbsDown className="h-3.5 w-3.5" />
              </button>
              {feedback !== null && (
                <span className="text-navy-900 font-bold text-[10px] ml-1 flex items-center gap-0.5">
                  <Check className="h-3 w-3 text-upay-yellow" /> Recorded
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
