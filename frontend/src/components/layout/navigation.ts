import {
  BarChart3,
  History,
  BookMarked,
  BrainCircuit,
  FlaskConical,
  Grid2x2,
  LayoutDashboard,
  ShieldQuestion,
  Swords,
  Trophy,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  description: string;
}

export interface NavSection {
  heading: string;
  items: NavItem[];
}

/** Sidebar structure, grouped so the theory and the lab tools stay distinct. */
export const NAV_SECTIONS: NavSection[] = [
  {
    heading: "Overview",
    items: [
      {
        to: "/dashboard",
        label: "Dashboard",
        icon: LayoutDashboard,
        description: "Summary of every study run so far",
      },
    ],
  },
  {
    heading: "Theory",
    items: [
      {
        to: "/game-theory",
        label: "Game Theory",
        icon: BrainCircuit,
        description: "The concepts behind the Prisoner's Dilemma",
      },
      {
        to: "/payoff-matrix",
        label: "Payoff Matrix",
        icon: Grid2x2,
        description: "Edit a matrix and see it analysed",
      },
      {
        to: "/strategies",
        label: "Strategies",
        icon: Swords,
        description: "The six tournament strategies",
      },
    ],
  },
  {
    heading: "Laboratory",
    items: [
      {
        to: "/match-simulator",
        label: "Match Simulator",
        icon: FlaskConical,
        description: "Run one iterated match",
      },
      {
        to: "/tournament",
        label: "Tournament",
        icon: Trophy,
        description: "Axelrod-style round robin",
      },
      {
        to: "/experiments",
        label: "Human Experiment",
        icon: Users,
        description: "Classroom sessions with real participants",
      },
    ],
  },
  {
    heading: "Analysis",
    items: [
      {
        to: "/history",
        label: "Game History",
        icon: History,
        description: "Everything played so far, in one list",
      },
      {
        to: "/statistics",
        label: "Statistics",
        icon: BarChart3,
        description: "Charts and descriptive statistics",
      },
      {
        to: "/trust-survey",
        label: "Trust Survey",
        icon: ShieldQuestion,
        description: "Expected cooperation versus what happened",
      },
      {
        to: "/about",
        label: "About / References",
        icon: BookMarked,
        description: "Sources and project background",
      },
    ],
  },
];
