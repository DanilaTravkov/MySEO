"use client";

import { Check, ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

export type AppSelectOption = {
  value: string;
  label: string;
};

type AppSelectProps = {
  ariaLabel: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  options: readonly AppSelectOption[];
  value: string;
};

export function AppSelect({ ariaLabel, disabled = false, onChange, options, value }: AppSelectProps) {
  const listboxId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  const [activeIndex, setActiveIndex] = useState(selectedIndex);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function closeOnOutsidePress(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("pointerdown", closeOnOutsidePress);
    return () => document.removeEventListener("pointerdown", closeOnOutsidePress);
  }, [open]);

  function choose(index: number) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setActiveIndex(index);
    setOpen(false);
    triggerRef.current?.focus();
  }

  function moveActive(step: number) {
    setActiveIndex((current) => (current + step + options.length) % options.length);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (disabled || options.length === 0) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setActiveIndex(selectedIndex);
        setOpen(true);
      } else {
        moveActive(event.key === "ArrowDown" ? 1 : -1);
      }
      return;
    }
    if (event.key === "Home" && open) {
      event.preventDefault();
      setActiveIndex(0);
      return;
    }
    if (event.key === "End" && open) {
      event.preventDefault();
      setActiveIndex(options.length - 1);
      return;
    }
    if ((event.key === "Enter" || event.key === " ") && open) {
      event.preventDefault();
      choose(activeIndex);
      return;
    }
    if (event.key === "Escape" && open) {
      event.preventDefault();
      setOpen(false);
    }
  }

  const selectedOption = options[selectedIndex];
  const activeOptionId = `${listboxId}-option-${activeIndex}`;

  return (
    <div
      className={`app-select${open ? " is-open" : ""}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
      ref={rootRef}
    >
      <button
        aria-activedescendant={open ? activeOptionId : undefined}
        aria-controls={listboxId}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
        className="app-select-trigger"
        disabled={disabled}
        onClick={() => {
          setActiveIndex(selectedIndex);
          setOpen((current) => !current);
        }}
        onKeyDown={handleKeyDown}
        ref={triggerRef}
        role="combobox"
        type="button"
      >
        <span>{selectedOption?.label ?? "Select"}</span>
        <ChevronDown aria-hidden="true" size={16} />
      </button>
      {open ? (
        <ul aria-label={ariaLabel} className="app-select-list" id={listboxId} role="listbox">
          {options.map((option, index) => (
            <li
              aria-selected={option.value === value}
              className={index === activeIndex ? "is-active" : undefined}
              id={`${listboxId}-option-${index}`}
              key={option.value}
              onClick={() => choose(index)}
              onMouseDown={(event) => event.preventDefault()}
              onMouseEnter={() => setActiveIndex(index)}
              role="option"
            >
              <span>{option.label}</span>
              {option.value === value ? <Check aria-hidden="true" size={15} /> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
