import { Outlet } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { Header } from './Header';

export function AppLayout() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <SidebarInset className="flex flex-col flex-1">
          <Header />
          <main className="flex-1 p-6 overflow-auto">
            <Outlet />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}