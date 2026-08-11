import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/common/Button";
import { Dialog } from "@/components/common/Dialog";
import { TextField } from "@/components/common/Field";
import { isApiError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});

const registerSchema = loginSchema.extend({
  full_name: z.string().min(1, "Enter your name"),
  password: z.string().min(8, "Passwords must be at least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

interface LoginDialogProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Sign in or create a student account.
 *
 * Registration through this dialog always produces a STUDENT: the backend
 * only grants TEACHER or ADMIN when an existing admin makes the request.
 */
export function LoginDialog({ open, onClose }: LoginDialogProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const { login, register: registerUser } = useAuth();
  const toast = useToast();

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", full_name: "" },
  });

  const close = () => {
    loginForm.reset();
    registerForm.reset();
    onClose();
  };

  const onLogin = loginForm.handleSubmit(async (values) => {
    try {
      const user = await login(values);
      toast.success("Signed in", `Welcome back, ${user.full_name}.`);
      close();
    } catch (error) {
      if (isApiError(error)) toast.apiError(error, "Sign in failed");
    }
  });

  const onRegister = registerForm.handleSubmit(async (values) => {
    try {
      const user = await registerUser({ ...values, role: "STUDENT" });
      toast.success("Account created", `Signed in as ${user.email}.`);
      close();
    } catch (error) {
      if (isApiError(error)) toast.apiError(error, "Registration failed");
    }
  });

  const isLogin = mode === "login";
  const submitting = isLogin
    ? loginForm.formState.isSubmitting
    : registerForm.formState.isSubmitting;

  return (
    <Dialog
      open={open}
      onClose={close}
      title={isLogin ? "Sign in" : "Create a student account"}
      description={
        isLogin
          ? "A teacher or admin account is needed to create tournaments and experiments."
          : "New accounts are created with the STUDENT role."
      }
      footer={
        <>
          <Button variant="ghost" onClick={close}>
            Cancel
          </Button>
          <Button onClick={isLogin ? onLogin : onRegister} loading={submitting}>
            {isLogin ? "Sign in" : "Create account"}
          </Button>
        </>
      }
    >
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          void (isLogin ? onLogin() : onRegister());
        }}
      >
        {isLogin ? (
          <>
            <TextField
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="teacher@example.com"
              error={loginForm.formState.errors.email?.message}
              {...loginForm.register("email")}
            />
            <TextField
              label="Password"
              type="password"
              autoComplete="current-password"
              error={loginForm.formState.errors.password?.message}
              {...loginForm.register("password")}
            />
          </>
        ) : (
          <>
            <TextField
              label="Full name"
              error={registerForm.formState.errors.full_name?.message}
              {...registerForm.register("full_name")}
            />
            <TextField
              label="Email"
              type="email"
              autoComplete="email"
              error={registerForm.formState.errors.email?.message}
              {...registerForm.register("email")}
            />
            <TextField
              label="Password"
              type="password"
              autoComplete="new-password"
              help="At least 8 characters."
              error={registerForm.formState.errors.password?.message}
              {...registerForm.register("password")}
            />
          </>
        )}

        <button
          type="button"
          onClick={() => setMode(isLogin ? "register" : "login")}
          className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
        >
          {isLogin ? "Need an account? Register instead" : "Already registered? Sign in"}
        </button>
      </form>
    </Dialog>
  );
}
