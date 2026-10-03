"use client";

import React from "react";

interface SafeMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Safe, zero-dangerouslySetInnerHTML Markdown renderer.
 * Converts markdown text into structured React nodes without HTML injection vulnerability.
 */
export function SafeMarkdown({ content, className = "" }: SafeMarkdownProps) {
  if (!content) return null;

  // Normalize headings so they form distinct blocks
  const normalized = content.replace(/(^|\n)(#{1,3}\s+[^\n]+)/g, "$1\n\n$2\n\n");
  const blocks = normalized.split(/\n\n+/).map((b) => b.trim()).filter(Boolean);

  return (
    <div className={`space-y-3 leading-relaxed text-slate-800 ${className}`}>
      {blocks.map((block, bIdx) => renderBlock(block, bIdx))}
    </div>
  );
}

function renderBlock(block: string, key: number): React.ReactNode {
  if (!block) return null;

  // 1. Code Block (``` ... ```)
  if (block.startsWith("```")) {
    const lines = block.split("\n");
    const code = lines.slice(1, lines[lines.length - 1].startsWith("```") ? -1 : undefined).join("\n");
    return (
      <pre
        key={key}
        className="rounded-lg bg-slate-900 p-3 text-xs text-slate-100 overflow-x-auto font-mono my-2"
      >
        <code>{code}</code>
      </pre>
    );
  }

  // 2. Headings (#, ##, ###)
  if (block.startsWith("### ")) {
    return (
      <h4 key={key} className="text-base font-semibold text-slate-900 mt-2">
        {renderInline(block.slice(4))}
      </h4>
    );
  }
  if (block.startsWith("## ")) {
    return (
      <h3 key={key} className="text-lg font-bold text-slate-900 mt-3">
        {renderInline(block.slice(3))}
      </h3>
    );
  }
  if (block.startsWith("# ")) {
    return (
      <h2 key={key} className="text-xl font-bold text-slate-900 mt-4">
        {renderInline(block.slice(2))}
      </h2>
    );
  }

  // 3. Blockquote (> text)
  if (block.startsWith("> ")) {
    const quoteText = block
      .split("\n")
      .map((l) => (l.startsWith("> ") ? l.slice(2) : l))
      .join(" ");
    return (
      <blockquote
        key={key}
        className="border-l-4 border-emerald-500 pl-3 py-1 italic text-slate-600 bg-emerald-50/50 rounded-r"
      >
        {renderInline(quoteText)}
      </blockquote>
    );
  }

  // 4. Unordered list (- or *)
  if (block.split("\n").every((l) => l.trim().startsWith("- ") || l.trim().startsWith("* "))) {
    const items = block.split("\n").map((l) => l.trim().replace(/^[-*]\s+/, ""));
    return (
      <ul key={key} className="list-disc list-inside space-y-1.5 pl-1">
        {items.map((item, iIdx) => (
          <li key={iIdx} className="text-sm">
            {renderInline(item)}
          </li>
        ))}
      </ul>
    );
  }

  // 5. Ordered list (1. 2. 3.)
  if (block.split("\n").every((l) => /^\d+\.\s+/.test(l.trim()))) {
    const items = block.split("\n").map((l) => l.trim().replace(/^\d+\.\s+/, ""));
    return (
      <ol key={key} className="list-decimal list-inside space-y-1.5 pl-1">
        {items.map((item, iIdx) => (
          <li key={iIdx} className="text-sm">
            {renderInline(item)}
          </li>
        ))}
      </ol>
    );
  }

  // 6. Regular paragraph with possible line breaks
  const lines = block.split("\n");
  return (
    <p key={key} className="text-sm leading-relaxed">
      {lines.map((line, lIdx) => (
        <React.Fragment key={lIdx}>
          {lIdx > 0 && <br />}
          {renderInline(line)}
        </React.Fragment>
      ))}
    </p>
  );
}

/**
 * Parse inline markdown tokens: bold, italic, code, links.
 * All HTML tags are escaped and rendered inert.
 */
function renderInline(text: string): React.ReactNode {
  if (!text) return null;

  // Tokenize regex for **bold**, *italic*, `code`, and [label](url)
  const tokenRegex = /(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, idx) => {
    if (!part) return null;

    // Bold
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={idx} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Italic
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      return (
        <em key={idx} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Inline code
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code
          key={idx}
          className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs text-emerald-800"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Link [label](url)
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/);
    if (linkMatch) {
      const [, label, rawUrl] = linkMatch;
      const cleanUrl = sanitizeUrl(rawUrl);
      if (cleanUrl) {
        return (
          <a
            key={idx}
            href={cleanUrl}
            target={cleanUrl.startsWith("http") ? "_blank" : undefined}
            rel={cleanUrl.startsWith("http") ? "noopener noreferrer" : undefined}
            className="text-emerald-600 underline hover:text-emerald-700 font-medium"
          >
            {label}
          </a>
        );
      }
      return <span key={idx}>{label}</span>;
    }

    // Plain text (inert text string)
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

/**
 * Enforce strict link URL allowlist (no javascript:, data:, vbscript:).
 */
function sanitizeUrl(url: string): string | null {
  const trimmed = url.trim();
  if (
    trimmed.startsWith("https://") ||
    trimmed.startsWith("http://") ||
    trimmed.startsWith("/") ||
    trimmed.startsWith("#")
  ) {
    return trimmed;
  }
  return null;
}
