import { useState } from "react";
import { BarChart3, BookOpen, Clock3, Folder, HelpCircle, Settings, Sparkles } from "lucide-react";
import { ChevronDown } from "lucide-react";

const SIDEBAR_LINKS = {
  left: [
    {
      label: "Conversations",
      icon: Sparkles,
      children: ["New conversation", "Recent chats"],
    },
    {
      label: "Library",
      icon: Folder,
      children: ["Saved prompts", "Shared chats"],
    },
  ],
  right: [
    {
      label: "Resources",
      icon: BookOpen,
      children: ["Knowledge base", "Prompt guide"],
    },
    {
      label: "Analytics",
      icon: BarChart3,
      children: ["Usage insights", "Model activity"],
    },
    {
      label: "Support",
      icon: HelpCircle,
      children: ["Help center", "Contact support"],
    },
    {
      label: "Preferences",
      icon: Settings,
      children: ["Settings", "Appearance"],
    },
  ],
};

export default function Sidebar({ side, onLinkClick }) {
  const [expanded, setExpanded] = useState(() =>
    Object.fromEntries(SIDEBAR_LINKS[side].map(({ label }) => [label, false]))
  );

  function toggleSection(label) {
    setExpanded((current) => ({
      ...current,
      [label]: !current[label],
    }));
  }

  return (
    <aside
      className={`absolute bottom-5 top-[84px] z-10 hidden w-48 flex-col rounded-2xl border border-[var(--chat-border)] bg-[var(--chat-surface)]/80 p-3 shadow-lg backdrop-blur-sm xl:flex ${
        side === "left" ? "left-5" : "right-5"
      }`}
    >
      <p className="px-3 pb-3 pt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--chat-muted)]">
        {side === "left" ? "Workspace" : "Explore"}
      </p>

      <nav className="flex flex-col gap-1" aria-label={`${side} sidebar`}>
        {SIDEBAR_LINKS[side].map(({ label, icon: Icon, children }) => (
          <div key={label}>
            <button
              type="button"
              onClick={() => toggleSection(label)}
              aria-expanded={expanded[label]}
              className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-xs font-medium text-[var(--chat-secondary)] transition-colors hover:bg-[var(--chat-soft)] hover:text-[var(--chat-text)]"
            >
              <span className="flex items-center gap-3">
                <Icon size={16} />
                <span>{label}</span>
              </span>
              <ChevronDown
                size={14}
                className={`transition-transform ${expanded[label] ? "" : "-rotate-90"}`}
              />
            </button>

            {expanded[label] && (
              <div className="ml-7 border-l border-[var(--chat-border)] pl-2">
                {children.map((child) => (
                  <button
                    key={child}
                    type="button"
                    onClick={() => onLinkClick(child)}
                    className="block w-full rounded-lg px-2 py-2 text-left text-[11px] text-[var(--chat-muted)] transition-colors hover:bg-[var(--chat-soft)] hover:text-[var(--chat-text)]"
                  >
                    {child}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
}
