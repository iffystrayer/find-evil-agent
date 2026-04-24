import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface BentoTileProps {
  children: ReactNode;
  span?: 1 | 2;  // 1x1 or 1x2 (width)
  tall?: boolean; // 2x1 (height)
  className?: string;
}

export const BentoTile = ({ children, span = 1, tall = false, className = '' }: BentoTileProps) => {
  const spanClass = span === 2 ? 'col-span-2' : 'col-span-1';
  const tallClass = tall ? 'row-span-2' : 'row-span-1';

  return (
    <motion.div
      className={`bento-tile ${spanClass} ${tallClass} ${className}`}
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      {children}
    </motion.div>
  );
};

interface BentoGridProps {
  children: ReactNode;
  columns?: 2 | 3 | 4;
}

export const BentoGrid = ({ children, columns = 2 }: BentoGridProps) => {
  const colsClass = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  }[columns];

  return (
    <div className={`grid ${colsClass} gap-4 auto-rows-[minmax(200px,auto)]`}>
      {children}
    </div>
  );
};
