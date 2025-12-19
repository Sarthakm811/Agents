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
      <SidebarHeader className="border-b border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <FlaskConical className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold">AI Research</h2>
            <p className="text-xs text-muted-foreground">Hybrid System</p>
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
      
      <SidebarFooter className="border-t border-sidebar-border p-4">
        <div className="text-xs text-muted-foreground">
          <p>Version 1.0.0</p>
          <p className="mt-1">© 2025 Hybrid AI Research</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}