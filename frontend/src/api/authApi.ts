/** Authentication endpoints. */

import { get, post } from "./client";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types";

export const authApi = {
  login: (payload: LoginRequest) => post<TokenResponse>("/auth/login", payload),

  register: (payload: RegisterRequest) => post<TokenResponse>("/auth/register", payload),

  me: () => get<User>("/auth/me"),
};
