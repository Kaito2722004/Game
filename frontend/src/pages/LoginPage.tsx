import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Dices, LogIn, ShieldCheck, UserPlus } from "lucide-react";
import { isApiError } from "@/api/client";
import { Button } from "@/components/common/Button";
import { TextField } from "@/components/common/Field";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import type { ApiError } from "@/types";

const loginSchema = z.object({
  email: z.string().min(1, "Enter your email").email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});

const registerSchema = z.object({
  full_name: z.string().min(1, "Enter your name"),
  email: z.string().min(1, "Enter your email").email("Enter a valid email address"),
  password: z.string().min(8, "Passwords must be at least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

interface LocationState {
  from?: string;
}

/**
 * Dedicated sign-in page.
 *
 * A full page rather than a modal: it is the first thing a teacher sees when
 * starting a session, and it gives room to explain what the roles mean.
 *
 * After signing in the user returns to whichever page sent them here, or the
 * dashboard if they came directly.
 */
export function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [failure, setFailure] = useState<ApiError | null>(null);

  const { login, register: registerUser, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();

  const returnTo = (location.state as LocationState | null)?.from ?? "/dashboard";

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "" },
  });

  const onLogin = loginForm.handleSubmit(async (values) => {
    setFailure(null);
    try {
      const signedIn = await login(values);
      toast.success("Signed in", `Welcome back, ${signedIn.full_name}.`);
      navigate(returnTo, { replace: true });
    } catch (error) {
      if (isApiError(error)) setFailure(error);
    }
  });

  const onRegister = registerForm.handleSubmit(async (values) => {
    setFailure(null);
    try {
      const created = await registerUser({ ...values, role: "STUDENT" });
      toast.success("Account created", `Signed in as ${created.email}.`);
      navigate(returnTo, { replace: true });
    } catch (error) {
      if (isApiError(error)) setFailure(error);
    }
  });

  const isLogin = mode === "login";
  const submitting = isLogin
    ? loginForm.formState.isSubmitting
    : registerForm.formState.isSubmitting;

  return (
    <div className="relative min-h-screen bg-lab-50 lg:grid lg:grid-cols-2">
      <div className="app-backdrop" aria-hidden />
      <div className="app-grain" aria-hidden />
      {/* Left: what this application is. Hidden on small screens. */}
      <aside className="relative z-10 hidden flex-col justify-between overflow-hidden border-r border-lab-250 bg-gradient-to-br from-lab-75 via-lab-100 to-[#1b0f33] px-10 py-12 text-white lg:flex">
        <div className="flex items-center gap-2.5">
          <span className="rounded-lg bg-violet-600 p-1.5" aria-hidden>
            <Dices className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold">Game Theory Lab</p>
            <p className="text-[11px] text-lab-500">Prisoner&apos;s Dilemma</p>
          </div>
        </div>

        <div className="max-w-md">
          <h1 className="text-3xl leading-snug font-semibold text-gradient">
            Prisoner&apos;s Dilemma Strategy Tournament
          </h1>
          <p className="mt-4 leading-relaxed text-lab-700">
            Analyse any payoff matrix, run Axelrod-style tournaments between six
            strategies, and record how real people play in a classroom experiment.
          </p>

          <dl className="mt-8 space-y-3 text-sm">
            {[
              ["Theory", "Dominance, Nash equilibria and Pareto comparison, computed from the numbers"],
              ["Simulation", "Iterated matches with an optional uncertain ending"],
              ["Experiment", "Simultaneous hidden choices with real participants"],
            ].map(([term, description]) => (
              <div key={term} className="border-l-2 border-violet-500/70 pl-3">
                <dt className="font-medium text-white">{term}</dt>
                <dd className="text-lab-600">{description}</dd>
              </div>
            ))}
          </dl>
        </div>

        <p className="text-xs text-lab-500">
          Based on Philip D. Straffin, <cite>Game Theory and Strategy</cite>
        </p>
      </aside>

      {/* Right: the form. */}
      <main className="relative z-10 flex min-h-screen flex-col justify-center px-5 py-10 sm:px-10 lg:min-h-0">
        <div className="mx-auto w-full max-w-md">
          {/* Compact brand for small screens, where the left panel is hidden. */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span className="rounded-lg bg-violet-600 p-1.5 text-white" aria-hidden>
              <Dices className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-lab-950">Game Theory Lab</p>
              <p className="text-[11px] text-lab-600">Prisoner&apos;s Dilemma</p>
            </div>
          </div>

          <h2 className="text-2xl font-semibold text-lab-950">
            {isLogin ? "Sign in" : "Create a student account"}
          </h2>
          <p className="mt-1.5 text-sm text-lab-700">
            {isLogin
              ? "Teacher and admin accounts can create tournaments and run classroom experiments."
              : "New accounts are created with the STUDENT role. Ask an administrator for teacher access."}
          </p>

          {isAuthenticated && user ? (
            <div className="mt-6 rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-4">
              <p className="text-sm font-medium text-emerald-200">
                You are already signed in as {user.full_name} ({user.role}).
              </p>
              <Button className="mt-3" size="sm" onClick={() => navigate("/dashboard")}>
                Go to the dashboard
              </Button>
            </div>
          ) : null}

          <form
            className="mt-6 space-y-4"
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
                  autoFocus
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
                  autoFocus
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

            {failure ? (
              <div role="alert" className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3">
                <p className="text-sm font-medium text-rose-200">
                  {failure.isNetworkError ? "Backend unreachable" : "Could not sign you in"}
                </p>
                <p className="mt-0.5 text-xs text-rose-300">{failure.message}</p>
                {failure.details.length > 0 ? (
                  <ul className="mt-1 list-inside list-disc text-xs text-rose-300">
                    {failure.details.map((detail, index) => (
                      <li key={index}>{detail}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}

            <Button
              type="submit"
              size="lg"
              fullWidth
              loading={submitting}
              icon={isLogin ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
            >
              {isLogin ? "Sign in" : "Create account"}
            </Button>
          </form>

          <button
            type="button"
            onClick={() => {
              setMode(isLogin ? "register" : "login");
              setFailure(null);
            }}
            className="mt-4 text-sm font-medium text-violet-400 hover:text-violet-300"
          >
            {isLogin
              ? "Need an account? Register instead"
              : "Already registered? Sign in instead"}
          </button>

          <div className="mt-8 rounded-xl border border-lab-250 bg-lab-100/70 p-4 backdrop-blur-sm">
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" aria-hidden />
              <div className="text-xs leading-relaxed text-lab-700">
                <p className="font-medium text-lab-900">Roles</p>
                <p className="mt-1">
                  <strong>ADMIN</strong> manages everything · <strong>TEACHER</strong> runs
                  tournaments and experiments · <strong>STUDENT</strong> reads results and
                  answers surveys.
                </p>
              </div>
            </div>
          </div>

          <Link
            to="/dashboard"
            className="mt-6 inline-flex items-center gap-1.5 text-sm text-lab-600 transition-colors hover:text-lab-900"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Continue without signing in
          </Link>
          <p className="mt-1 text-xs text-lab-500">
            Every page can be read while signed out. Only creating and running things
            needs an account.
          </p>
        </div>
      </main>
    </div>
  );
}
