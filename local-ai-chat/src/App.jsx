
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  Brain,
  Moon,
  Sun,
  Circle,
  Command,
  Plus,
  Send,
  Sparkles,
  User,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import "./App.css";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const API_URL = import.meta.env.VITE_API_BASE_URL;

const SUGGESTIONS = [
  {
    title: "Understand a concept",
    prompt: "Explain embeddings in simple terms.",
    icon: Brain,
  },
  {
    title: "Write some code",
    prompt: "Show me a clean Python function with error handling.",
    icon: Command,
  },
  {
    title: "Explore an idea",
    prompt: "Give me three practical AI project ideas.",
    icon: Sparkles,
  },
];

export default function App() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("local-ai-theme");
      if (saved === "light" || saved === "dark") return saved;
    } catch { /* Storage may be unavailable in private browsing. */ }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.style.colorScheme = theme;
    try { localStorage.setItem("local-ai-theme", theme); } catch { /* Keep the toggle usable without storage. */ }
  }, [theme]);

  const [mode, setMode] = useState("with-memory");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const conversationRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const panel = conversationRef.current;
    if (panel) {
      panel.scrollTo({
        top: panel.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  function handleModeChange(value) {
    setMode(value);
    setMessages([]);
    setQuestion("");
    setError("");
  }

  function startNewChat() {
    if (loading) return;

    setMessages([]);
    setQuestion("");
    setError("");
    inputRef.current?.focus();
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const text = question.trim();
    if (!text || loading) return;

    const userMessage = {
      role: "user",
      content: text,
    };

    const history = [...messages, userMessage];

    setMessages(history);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const endpoint =
        mode === "with-memory"
          ? "/chat/with-memory"
          : "/chat/no-memory";

      // Memory mode sends conversation history.
      // No-memory mode sends only the current question.
      const requestMessages =
        mode === "with-memory"
          ? history
          : [userMessage];

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: requestMessages,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || `API error: ${response.status}`
        );
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (err) {
      setError(
        `${err.message}. Check that FastAPI and Ollama are running.`
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function useSuggestion(prompt) {
    setQuestion(prompt);
    inputRef.current?.focus();
  }

  return (
    <main data-theme={theme} className="chat-app relative flex h-dvh min-h-[520px] flex-col overflow-hidden bg-[var(--chat-page)] text-[var(--chat-text)]">
      {/* Ambient background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -top-48 left-1/2 h-96 w-[38rem] -translate-x-1/2 rounded-full bg-violet-700/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-indigo-600/5 blur-[100px]" />
      </div>

      {/* Top navigation */}
      <header className="relative z-10 flex h-[68px] shrink-0 items-center justify-between border-b border-[var(--chat-border)] px-4 sm:px-7">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-400/20 bg-violet-500/10 text-[var(--chat-accent)]">
            <Sparkles size={21} />
          </div>

          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold tracking-tight sm:text-base">
              Local AI
            </h1>
            <p className="text-xs text-[var(--chat-muted)]">
              Your private workspace
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="theme-toggle h-9 w-9 rounded-xl p-0"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </Button>
          <div className="hidden items-center gap-2 rounded-full border border-[var(--chat-border)] bg-[var(--chat-soft)] px-3 py-1.5 text-xs text-[var(--chat-muted)] sm:flex">
            <Circle
              size={7}
              className="fill-emerald-400 text-emerald-400"
            />
            Local model
          </div>

          <Button
            type="button"
            variant="ghost"
            onClick={startNewChat}
            aria-label="Start a new chat"
            disabled={loading}
            className="h-9 gap-2 rounded-lg text-[var(--chat-secondary)] hover:bg-[var(--chat-soft)] hover:text-[var(--chat-text)]"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">New chat</span>
          </Button>
        </div>
      </header>

      {/* Main conversation */}
      <div className="relative z-10 mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col px-3 py-3 sm:px-6 sm:py-5">
        <Card className="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-surface)] py-0 shadow-xl shadow-black/5 ring-0 dark:shadow-black/20">
          {/* Conversation toolbar */}
          <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--chat-border)] px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--chat-soft)] text-[var(--chat-secondary)]">
                <Bot size={18} />
              </div>

              <div>
                <p className="text-sm font-medium">Qwen 3.5</p>
                <p className="text-[11px] text-[var(--chat-muted)]">
                  Powered by Ollama
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Brain
                size={16}
                className={
                  mode === "with-memory"
                    ? "text-[var(--chat-accent)]"
                    : "text-[var(--chat-muted)]"
                }
              />

              <Select
                value={mode}
                onValueChange={handleModeChange}
                disabled={loading}
              >
                <SelectTrigger
                  aria-label="Conversation memory mode"
                  className="h-9 w-[158px] border-[var(--chat-border)] bg-[var(--chat-soft)] text-xs shadow-none focus:ring-violet-400/30 sm:w-[175px]"
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="with-memory">
                    With memory
                  </SelectItem>
                  <SelectItem value="no-memory">
                    Without memory
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Scrollable messages */}
          <CardContent
            ref={conversationRef}
            role="log"
            aria-label="Conversation messages"
            aria-live="polite"
            className="flex min-h-0 flex-1 flex-col gap-7 overflow-y-auto overscroll-contain px-4 py-6 sm:px-8 sm:py-8 lg:px-16"
          >
            {messages.length === 0 ? (
              <div className="my-auto flex w-full flex-col items-center justify-center py-8 text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-violet-400/20 bg-gradient-to-br from-violet-500/15 to-indigo-500/10 text-[var(--chat-accent)] shadow-lg shadow-violet-950/20">
                  <Sparkles size={27} />
                </div>

                <p className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-[var(--chat-accent)]">
                  Ready when you are
                </p>

                <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                  What can we explore?
                </h2>

                <p className="mt-3 max-w-md text-sm leading-6 text-[var(--chat-muted)]">
                  Chat with your local model, experiment with context,
                  and learn how AI applications work.
                </p>

                <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-3">
                  {SUGGESTIONS.map((item) => {
                    const Icon = item.icon;

                    return (
                      <button
                        key={item.title}
                        type="button"
                        onClick={() => useSuggestion(item.prompt)}
                        className="group rounded-xl border border-[var(--chat-border)] bg-[var(--chat-soft)] p-4 text-left transition-all hover:border-violet-400/30 hover:bg-violet-500/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60"
                      >
                        <Icon
                          size={18}
                          className="mb-4 text-[var(--chat-muted)] transition-colors group-hover:text-[var(--chat-accent)]"
                        />
                        <p className="text-sm font-medium text-[var(--chat-text)]">
                          {item.title}
                        </p>
                        <p className="mt-1.5 text-xs leading-5 text-[var(--chat-muted)]">
                          {item.prompt}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
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
                    {message.role === "user" ? (
                      <User size={16} />
                    ) : (
                      <Bot size={17} />
                    )}
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
              ))
            )}

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
          </CardContent>

          {/* Message composer */}
          <div className="shrink-0 border-t border-[var(--chat-border)] bg-[var(--chat-footer)] px-3 pb-3 pt-4 sm:px-6 sm:pb-4">
            <form
              onSubmit={handleSubmit}
              className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-input)] p-2 transition-colors focus-within:border-violet-400/40 focus-within:ring-2 focus-within:ring-violet-400/[0.07]"
            >
              <Input
                ref={inputRef}
                aria-label="Your message"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask anything..."
                disabled={loading}
                autoComplete="off"
                className="h-11 min-w-0 flex-1 border-0 bg-transparent px-3 text-sm text-[var(--chat-text)] shadow-none placeholder:text-[var(--chat-muted)] focus-visible:ring-0 dark:bg-transparent"
              />

              <Button
                type="submit"
                aria-label="Send message"
                disabled={loading || !question.trim()}
                className="h-10 w-10 shrink-0 rounded-xl bg-violet-600 p-0 text-white transition-colors hover:bg-violet-500 disabled:bg-[var(--chat-soft)] disabled:text-slate-600"
              >
                <Send size={17} />
              </Button>
            </form>

            <div className="mx-auto mt-3 flex max-w-3xl flex-wrap items-center justify-between gap-2 px-1 text-[11px] text-[var(--chat-muted)]">
              <span className="flex items-center gap-1.5">
                <Zap size={12} />
                Runs on your local model
              </span>

              <span>
                {mode === "with-memory"
                  ? "Conversation history included"
                  : "Each request starts fresh"}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </main>
  );
}
