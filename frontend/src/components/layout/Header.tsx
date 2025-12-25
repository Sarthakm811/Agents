import { SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Bell, User, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';

export function Header() {
  return (
    <header className="sticky top-0 z-50 flex h-16 items-center gap-4 px-6 shadow-lg border-b bg-gradient-to-r from-background via-primary/5 to-background backdrop-blur-xl supports-[backdrop-filter]:bg-background/70 overflow-hidden group">
      {/* Animated background gradient */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-secondary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Decorative animated line at bottom */}
      <motion.div
        className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-primary via-secondary to-accent"
        initial={{ scaleX: 0, originX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.8, delay: 0.1 }}
      />

      <SidebarTrigger className="hover:bg-primary/20 hover:text-primary transition-all duration-300 rounded-lg" />

      {/* Center branding area */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex items-center gap-2 ml-2"
      >
        <Sparkles className="h-4 w-4 text-primary animate-spin" style={{ animationDuration: '3s' }} />
        <span className="text-xs font-semibold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          AI Research System
        </span>
      </motion.div>

      <div className="flex-1" />

      {/* Action buttons */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
        className="flex items-center gap-1"
      >
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
          <Button
            variant="ghost"
            size="icon"
            className="relative hover:bg-gradient-to-br hover:from-primary/20 hover:to-secondary/20 transition-all duration-300 rounded-lg group/bell"
          >
            <motion.div
              animate={{ y: [ 0, -2, 0 ] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Bell className="h-5 w-5 group-hover/bell:text-primary transition-colors" />
            </motion.div>
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs animate-pulse shadow-lg shadow-red-500/50"
            >
              3
            </Badge>
          </Button>
        </motion.div>

        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
          <Button
            variant="ghost"
            size="icon"
            className="hover:bg-gradient-to-br hover:from-accent/20 hover:to-primary/20 transition-all duration-300 rounded-lg group/user"
          >
            <User className="h-5 w-5 group-hover/user:text-accent transition-colors" />
          </Button>
        </motion.div>
      </motion.div>
    </header>
  );
}