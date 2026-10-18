import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, User } from "lucide-react";

export default function Messages({ messages, loading, error }) {
  return (
    <>
      {messages.map((message, index) => (
        <div
          key={`${index}-${message.role}`}
          className={`flex items-start gap-3 ${
            message.role === "user" ? "flex-row-reverse" : ""
          }`}
        >
          <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
              message.role === "user"
                ? "bg-violet-500/15 text-[var(--chat-accent)]"
                : "border border-[var(--chat-border)] bg-[var(--chat-soft)] text-[var(--chat-secondary)]"
            }`}
          >
            {message.role === "user" ? <User size={16} /> : <Bot size={17} />}
          </div>

          <div
            className={`min-w-0 max-w-[88%] [overflow-wrap:anywhere] text-sm leading-7 sm:max-w-[80%] ${
              message.role === "user"
                ? "whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-violet-600 px-4 py-3 text-white"
                : "chat-markdown pt-1 text-[var(--chat-text)]"
            }`}
          >
            {message.role === "user" ? message.content : (
              <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        </div>
      ))}

      {loading && (
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--chat-border)] bg-[var(--chat-soft)] text-[var(--chat-accent)]">
            <Bot size={17} />
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-[var(--chat-soft)] px-3 py-2.5 text-sm text-[var(--chat-muted)]">
            <span className="flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300 [animation-delay:-0.2s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300 [animation-delay:-0.1s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300" />
            </span>
            Thinking
          </div>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="ml-11 rounded-xl border border-red-400/20 bg-red-400/[0.06] px-4 py-3 text-sm leading-6 text-red-700 dark:text-red-300"
        >
          {error}
        </div>
      )}
    </>
  );
}
