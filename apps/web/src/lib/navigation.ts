import {
  BarChart3,
  Activity,
  Compass,
  FlaskConical,
  LayoutDashboard,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavigationItem {
  href: string;
  label: string;
  icon: LucideIcon;
  level?: "advanced";
}

export const navigationItems: NavigationItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/opportunities", label: "Opportunities", icon: BarChart3 },
  { href: "/distributions", label: "Distribution lab", icon: FlaskConical, level: "advanced" },
  { href: "/monitoring", label: "Monitoring", icon: Activity, level: "advanced" },
  { href: "/settings", label: "Settings", icon: Settings },
];
