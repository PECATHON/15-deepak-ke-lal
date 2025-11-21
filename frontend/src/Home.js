import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { IoChatbubbles, IoCalendar, IoBook, IoNotifications, IoBulb, IoPeople, IoArrowForward } from 'react-icons/io5';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: IoCalendar,
      title: 'Smart Travel Planning',
      description: 'Plan your trips with AI-powered itinerary suggestions and real-time updates.',
      color: '#2b5278',
    },
    {
      icon: IoBook,
      title: 'Destination Guides',
      description: 'Get comprehensive travel guides, tips, and local insights for any destination.',
      color: '#3d4a3a',
    },
    {
      icon: IoNotifications,
      title: 'Flight Tracking',
      description: 'Real-time flight updates, price alerts, and booking recommendations.',
      color: '#2b5278',
    },
    {
      icon: IoBulb,
      title: 'AI-Powered Assistant',
      description: 'Get intelligent travel recommendations tailored to your preferences.',
      color: '#3d4a3a',
    },
    {
      icon: IoChatbubbles,
      title: '24/7 Support',
      description: 'Ask questions anytime and get instant answers about your travel plans.',
      color: '#2b5278',
    },
    {
      icon: IoPeople,
      title: 'Multi-Agent System',
      description: 'Specialized agents work together to plan your perfect journey.',
      color: '#3d4a3a',
    },
  ];

  return (
    <div className="home-container">
      {/* Animated background gradient */}
      <div className="animated-bg" />
      
      {/* Hero Section */}
      <section className="hero-section">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="hero-content"
        >
          {/* Logo/Icon */}
          <motion.div
            className="hero-icon"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            <IoChatbubbles size={60} />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="hero-title"
          >
            Meet <span className="gradient-text">Chat &amp; Go</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hero-subtitle"
          >
            Your intelligent travel companion for flights, hotels, destinations, and more.
          </motion.p>

          {/* Single centered CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="cta-single"
          >
            <motion.button
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="btn-primary btn-centered"
              onClick={() => navigate('/chat')}
            >
              <IoChatbubbles size={20} />
              Start Planning
              <IoArrowForward size={20} />
            </motion.button>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true, margin: "-100px" }}
          className="features-header"
        >
          <h2 className="section-title">
            Powerful Features
          </h2>
          <p className="section-subtitle">
            Discover how Chat &amp; Go transforms your travel planning experience
          </p>
        </motion.div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              viewport={{ once: true }}
              className="feature-card"
            >
              <div className="feature-icon" style={{ backgroundColor: feature.color }}>
                <feature.icon size={28} />
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p>&copy; 2024 Chat &amp; Go. Your AI Travel Companion.</p>
          <p className="footer-subtitle">Powered by Multi-Agent AI System</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
