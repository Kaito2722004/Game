import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from "react";
import { InfoTooltip } from "./InfoTooltip";

interface FieldShellProps {
  label: string;
  hint?: string;
  error?: string;
  help?: string;
  htmlFor: string;
  children: ReactNode;
}

function FieldShell({ label, hint, error, help, htmlFor, children }: FieldShellProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5">
        <label htmlFor={htmlFor} className="text-sm font-medium text-lab-800">
          {label}
        </label>
        {hint ? <InfoTooltip text={hint} label={`About ${label}`} /> : null}
      </div>
      {children}
      {help && !error ? <p className="text-xs text-lab-600">{help}</p> : null}
      {error ? (
        <p role="alert" className="text-xs font-medium text-rose-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}

const CONTROL_CLASS =
  "w-full rounded-xl border border-lab-300 bg-lab-50/60 px-3 py-2 text-sm text-lab-900 " +
  "transition-all duration-200 placeholder:text-lab-500 hover:border-lab-400/60 " +
  "focus:border-violet-500 focus:bg-lab-50 focus:shadow-[0_0_0_3px_rgb(139_92_246/0.15)] " +
  "disabled:cursor-not-allowed disabled:bg-lab-200 disabled:text-lab-500";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
  help?: string;
}

export function TextField({ label, hint, error, help, id, ...rest }: TextFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return (
    <FieldShell label={label} hint={hint} error={error} help={help} htmlFor={fieldId}>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        className={CONTROL_CLASS}
        {...rest}
      />
    </FieldShell>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  hint?: string;
  error?: string;
  help?: string;
  children: ReactNode;
}

export function SelectField({
  label,
  hint,
  error,
  help,
  id,
  children,
  ...rest
}: SelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return (
    <FieldShell label={label} hint={hint} error={error} help={help} htmlFor={fieldId}>
      <select
        id={fieldId}
        aria-invalid={error ? true : undefined}
        className={CONTROL_CLASS}
        {...rest}
      >
        {children}
      </select>
    </FieldShell>
  );
}

interface CheckboxFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  description?: string;
}

export function CheckboxField({ label, description, id, ...rest }: CheckboxFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return (
    <div className="flex items-start gap-2.5">
      <input
        id={fieldId}
        type="checkbox"
        className="mt-0.5 h-4 w-4 rounded border-lab-300 text-violet-400"
        {...rest}
      />
      <div>
        <label htmlFor={fieldId} className="text-sm font-medium text-lab-800">
          {label}
        </label>
        {description ? <p className="text-xs text-lab-600">{description}</p> : null}
      </div>
    </div>
  );
}
