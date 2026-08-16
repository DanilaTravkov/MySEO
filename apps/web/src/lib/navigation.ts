import {
  BarChart3,
  Cloud,
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
  { href: "/distributions", label: "Distribution lab", icon: FlaskConical },
  { href: "/functions", label: "Cloud functions", icon: Cloud, level: "advanced" },
  { href: "/settings", label: "Settings", icon: Settings },
];
