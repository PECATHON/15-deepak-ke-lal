import React from 'react';
import { motion } from 'framer-motion';
import { IoSparkles } from 'react-icons/io5';

const LoadingSpinner = ({ text = "Loading...", size = "medium" }) => {
  const sizeClasses = {
    small: 'loading-small',
    medium: 'loading-medium',
    large: 'loading-large'
  };

  return (
    <motion.div 
      className={`loading-container ${sizeClasses[size]}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="loading-spinner"
        animate={{ rotate: 360 }}
        transition={{ 
          duration: 2,
          repeat: Infinity,
          ease: "linear"
        }}
      >
        <IoSparkles />
      </motion.div>
      
      <motion.div
        className="loading-dots"
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
        transition={{
          duration: 0.8,
          repeat: Infinity,
          repeatType: "reverse"
        }}
      >
        {text}
      </motion.div>
      
      <motion.div className="loading-bar">
        <motion.div 
          className="loading-progress"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </motion.div>
    </motion.div>
  );
};

export default LoadingSpinner;