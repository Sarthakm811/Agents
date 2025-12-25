import { Link, useLocation } from 'react-router-dom';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/components/ui/sidebar';
import {
  LayoutDashboard,
  FileText,
  Settings,
  Activity,
  Shield,
  Sparkles,
  FlaskConical
} from 'lucide-react';

const menuItems = [
  { title: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { title: 'New Research', icon: Sparkles, path: '/new' },
  { title: 'Active Sessions', icon: Activity, path: '/sessions' },
  { title: 'Results', icon: FileText, path: '/results' },
  { title: 'Ethics & Compliance', icon: Shield, path: '/ethics' },
  { title: 'Settings', icon: Settings, path: '/settings' },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border p-6 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary text-primary-foreground shadow-lg">
            <FlaskConical className="h-7 w-7" />
          </div>
          <div>
            <h2 className="text-lg font-bold">AI Research</h2>
            <p className="text-xs text-muted-foreground font-medium">Hybrid System</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.path}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.path}
                  >
                    <Link to={item.path}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-4 bg-gradient-to-br from-muted/30 to-transparent">
        <div className="text-xs text-muted-foreground">
          <p className="font-medium">Version 1.0.0</p>
          <p className="mt-1">© 2025 Hybrid AI Research</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}