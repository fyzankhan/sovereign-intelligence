import { Brain, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function MessageForm({
  inputRef,
  question,
  onQuestionChange,
  onSubmit,
  mode,
  onModeChange,
  modeOptions,
  loading,
}) {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-3 flex items-center justify-end gap-2">
        <Brain
          size={16}
          className={
            mode === "with-memory"
              ? "text-[var(--chat-accent)]"
              : "text-[var(--chat-muted)]"
          }
        />

        <Select value={mode} onValueChange={onModeChange} disabled={loading}>
          <SelectTrigger
            aria-label="Conversation memory mode"
            className="h-9 w-[158px] border-[var(--chat-border)] bg-[var(--chat-soft)] text-xs shadow-none focus:ring-violet-400/30 sm:w-[175px]"
          >
            <SelectValue />
          </SelectTrigger>

          <SelectContent>
            {modeOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <form
        onSubmit={onSubmit}
        className="flex items-end gap-2 rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-input)] p-2 transition-colors focus-within:border-violet-400/40 focus-within:ring-2 focus-within:ring-violet-400/[0.07]"
      >
        <Input
          ref={inputRef}
          aria-label="Your message"
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
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
    </div>
  );
}
