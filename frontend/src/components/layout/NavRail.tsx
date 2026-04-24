import { motion } from 'framer-motion';
import { Home, Search, Activity, BarChart3, Settings, Info } from 'lucide-react';
import { useState } from 'react';

interface NavItem {
  id: string;
  icon: React.ElementType;
  label: string;
  badge?: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', icon: Home, label: 'Dashboard' },
  { id: 'analyze', icon: Search, label: 'Single Analysis' },
  { id: 'investigate', icon: Activity, label: 'Investigate' },
  { id: 'reports', icon: BarChart3, label: 'Reports' },
  { id: 'settings', icon: Settings, label: 'Settings' },
  { id: 'about', icon: Info, label: 'About' },
];

export const NavRail = () => {
  const [activeItem, setActiveItem] = useState('dashboard');

  return (
    <motion.nav
      className="glass-panel m-4 w-20 flex flex-col items-center py-6 gap-4"
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {/* Logo */}
      <motion.div
        className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-6"
        whileHover={{ scale: 1.1, rotate: 5 }}
        whileTap={{ scale: 0.95 }}
      >
        <span className="text-2xl font-bold">🔍</span>
      </motion.div>

      {/* Nav Items */}
      <div className="flex-1 flex flex-col gap-3">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;

          return (
            <motion.button
              key={item.id}
              onClick={() => setActiveItem(item.id)}
              className={`
                relative w-14 h-14 rounded-xl flex items-center justify-center
                transition-all duration-300
                ${isActive
                  ? 'bg-purple-500/30 border border-purple-400/50'
                  : 'hover:bg-white/10 border border-transparent'
                }
              `}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 + index * 0.05 }}
            >
              <Icon
                className={`w-6 h-6 ${isActive ? 'text-purple-300' : 'text-gray-400'}`}
              />

              {/* Badge */}
              {item.badge && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center">
                  {item.badge}
                </span>
              )}

              {/* Tooltip */}
              <div className="absolute left-full ml-3 px-3 py-1 bg-black/80 rounded-lg text-sm whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity">
                {item.label}
              </div>
            </motion.button>
          );
        })}
      </div>
    </motion.nav>
  );
};
