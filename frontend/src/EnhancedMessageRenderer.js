import React from 'react';
import './EnhancedChat.css';

/**
 * Enhanced Message Renderer
 * 
 * Renders rich, multi-modal content for travel search results including:
 * - Multi-leg flight itineraries with layovers
 * - Price comparisons across providers
 * - Hotel images and virtual tours
 * - Maps and booking links
 * - Booking simulations
 * - User preferences
 */

const EnhancedMessageRenderer = ({ content }) => {
  // Try to parse JSON content
  let data = null;
  let isJSON = false;
  
  try {
    data = JSON.parse(content);
    isJSON = true;
  } catch {
    // Not JSON, render as plain text
    return <div className="message-text">{content}</div>;
  }
  
  if (!isJSON || !data.success) {
    return <div className="message-text">{content}</div>;
  }
  
  // Render based on content type
  if (data.flights) {
    return <FlightResults data={data} />;
  } else if (data.hotels) {
    return <HotelResults data={data} />;
  } else if (data.booking) {
    return <BookingConfirmation data={data} />;
  } else if (data.user_profile) {
    return <UserPreferences data={data} />;
  }
  
  return <div className="message-text">{content}</div>;
};

// Flight Results Component
const FlightResults = ({ data }) => {
  const { flights, trip_type, comparison, price_alerts, user_preferences } = data;
  
  return (
    <div className="enhanced-results">
      <div className="results-header">
        <h3>✈️ Flight Search Results</h3>
        {trip_type === 'round-trip' && <span className="round-trip-badge">Round Trip</span>}
        <p>{data.query} • {flights.length} options found</p>
      </div>
      
      {/* Price Alerts */}
      {price_alerts && price_alerts.length > 0 && (
        <div className="price-alert">
          🔔 {price_alerts[0].message}
        </div>
      )}
      
      {/* Comparison Section */}
      {comparison && (
        <div className="comparison-section">
          <div className="comparison-title">Quick Comparison</div>
          <div className="comparison-items">
            <div className="comparison-item">
              <strong>💰 Cheapest</strong>
              {comparison.cheapest.flight_id} - ₹{comparison.cheapest.prices[user_preferences?.seat_class || 'Economy']}
            </div>
            <div className="comparison-item">
              <strong>⚡ Fastest</strong>
              {comparison.fastest.flight_id} - {comparison.fastest.total_duration}
            </div>
          </div>
        </div>
      )}
      
      {/* Flight Options */}
      {flights.map((flight, idx) => (
        <div key={idx} className="flight-card">
          {flight.type === 'round-trip' ? (
            <RoundTripFlight flight={flight} userClass={user_preferences?.seat_class} />
          ) : (
            <SingleFlight flight={flight} userClass={user_preferences?.seat_class} />
          )}
        </div>
      ))}
      
      {/* Map Link */}
      {data.map_link && (
        <a href={data.map_link} target="_blank" rel="noopener noreferrer" className="map-link">
          🗺️ View Route on Map
        </a>
      )}
    </div>
  );
};

// Single Flight Component
const SingleFlight = ({ flight, userClass = 'Economy' }) => {
  const price = flight.prices?.[userClass] || flight.prices?.Economy || 0;
  
  return (
    <div className="flight-details">
      <div className="flight-header">
        <h4>{flight.type === 'direct' ? '🎯 Direct Flight' : `🔄 ${flight.layovers}-Stop Flight`}</h4>
        <div className="flight-price">₹{price.toLocaleString()}</div>
      </div>
      
      {/* Flight Legs */}
      <div className="flight-legs">
        {flight.legs.map((leg, idx) => (
          <div key={idx} className="flight-leg">
            <div className="leg-header">
              ✈️ Leg {leg.leg_number}: {leg.airline} {leg.flight_number}
            </div>
            <div className="leg-details">
              <div><strong>From:</strong> {leg.origin}</div>
              <div><strong>To:</strong> {leg.destination}</div>
              <div><strong>Departure:</strong> {leg.departure_time}</div>
              <div><strong>Arrival:</strong> {leg.arrival_time}</div>
              <div><strong>Duration:</strong> {leg.duration}</div>
              <div><strong>Aircraft:</strong> {leg.aircraft}</div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Layover Info */}
      {flight.layover_info && flight.layover_info.length > 0 && (
        <div className="layover-info">
          <strong>⏱️ Layover:</strong> {flight.layover_info[0].airport} - {flight.layover_info[0].duration}
          <div style={{fontSize: '12px', marginTop: '5px'}}>
            Facilities: {flight.layover_info[0].facilities.join(', ')}
          </div>
        </div>
      )}
      
      {/* Price Comparison */}
      {flight.providers && (
        <div>
          <div style={{fontWeight: 'bold', margin: '10px 0 5px 0'}}>💳 Price Comparison:</div>
          <div className="price-comparison">
            {flight.providers.map((provider, idx) => (
              <a 
                key={idx} 
                href={provider.link} 
                target="_blank" 
                rel="noopener noreferrer"
                className={`provider-card ${provider.name === flight.cheapest_provider ? 'cheapest' : ''}`}
              >
                <div className="provider-name">{provider.name}</div>
                <div className="provider-price">₹{provider.price.toLocaleString()}</div>
              </a>
            ))}
          </div>
        </div>
      )}
      
      {/* Amenities */}
      {flight.amenities && (
        <div className="amenities">
          {flight.amenities.map((amenity, idx) => (
            <span key={idx} className="amenity-badge">{amenity}</span>
          ))}
        </div>
      )}
      
      {/* Booking Link */}
      {flight.booking_link && (
        <a href={flight.booking_link} target="_blank" rel="noopener noreferrer" className="booking-btn">
          📅 Book Now
        </a>
      )}
    </div>
  );
};

// Round Trip Flight Component
const RoundTripFlight = ({ flight, userClass = 'Economy' }) => {
  const price = flight.total_price?.[userClass] || 0;
  
  return (
    <div className="flight-details">
      <div className="flight-header">
        <h4>🔄 Round Trip</h4>
        <div className="flight-price">
          ₹{price.toLocaleString()}
          {flight.savings && <div style={{fontSize: '12px', color: '#4caf50'}}>Save {flight.savings}</div>}
        </div>
      </div>
      
      <div style={{marginBottom: '15px'}}>
        <strong>✈️ Outbound:</strong>
        <SingleFlight flight={flight.outbound} userClass={userClass} />
      </div>
      
      <div>
        <strong>🏠 Return:</strong>
        <SingleFlight flight={flight.inbound} userClass={userClass} />
      </div>
      
      {flight.booking_link && (
        <a href={flight.booking_link} target="_blank" rel="noopener noreferrer" className="booking-btn">
          📅 Book Round Trip
        </a>
      )}
    </div>
  );
};

// Hotel Results Component
const HotelResults = ({ data }) => {
  const { hotels, location, nights, comparison, price_alerts } = data;
  
  return (
    <div className="enhanced-results">
      <div className="results-header">
        <h3>🏨 Hotel Search Results</h3>
        <p>{location} • {nights} night{nights > 1 ? 's' : ''} • {hotels.length} options</p>
      </div>
      
      {/* Price Alerts */}
      {price_alerts && price_alerts.length > 0 && (
        <div className="price-alert">
          🔔 {price_alerts[0].alert_message}
        </div>
      )}
      
      {/* Comparison */}
      {comparison && (
        <div className="comparison-section">
          <div className="comparison-title">Top Picks</div>
          <div className="comparison-items">
            <div className="comparison-item">
              <strong>💰 Best Value</strong>
              {comparison.cheapest.name}
            </div>
            <div className="comparison-item">
              <strong>⭐ Highest Rated</strong>
              {comparison.highest_rated.name} ({comparison.highest_rated.rating}★)
            </div>
          </div>
        </div>
      )}
      
      {/* Hotels */}
      {hotels.map((hotel, idx) => (
        <div key={idx} className="hotel-card">
          <div className="hotel-header">
            <h4>{hotel.name}</h4>
            <div className="star-rating">
              {'⭐'.repeat(hotel.stars)} ({hotel.rating})
            </div>
          </div>
          
          {/* Images */}
          {hotel.images && hotel.images.length > 0 && (
            <div className="image-gallery">
              {hotel.images.map((img, idx) => (
                <img key={idx} src={img} alt={hotel.name} className="hotel-image" />
              ))}
            </div>
          )}
          
          <div><strong>📍 Location:</strong> {hotel.location}</div>
          <div><strong>👥 Reviews:</strong> {hotel.reviews.toLocaleString()}</div>
          {hotel.review_snippet && <div style={{fontStyle: 'italic', color: '#666', margin: '5px 0'}}>"{hotel.review_snippet}"</div>}
          
          {/* Price Comparison */}
          <div style={{fontWeight: 'bold', margin: '10px 0 5px 0'}}>💳 Price per night:</div>
          <div className="price-comparison">
            {Object.entries(hotel.prices_per_night).map(([provider, price]) => (
              <a 
                key={provider}
                href={hotel.booking_links?.[provider] || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className={`provider-card ${provider === hotel.cheapest_provider ? 'cheapest' : ''}`}
              >
                <div className="provider-name">{provider}</div>
                <div className="provider-price">₹{price.toLocaleString()}</div>
              </a>
            ))}
          </div>
          
          {/* Amenities */}
          {hotel.amenities && (
            <div className="amenities">
              {hotel.amenities.map((amenity, idx) => (
                <span key={idx} className="amenity-badge">{amenity}</span>
              ))}
            </div>
          )}
          
          {/* Virtual Tour */}
          {hotel.virtual_tour && (
            <a href={hotel.virtual_tour} target="_blank" rel="noopener noreferrer" className="virtual-tour-btn">
              🏛️ Virtual Tour
            </a>
          )}
          
          {/* Map Link */}
          {hotel.map_link && (
            <a href={hotel.map_link} target="_blank" rel="noopener noreferrer" className="map-link">
              🗺️ View on Map
            </a>
          )}
        </div>
      ))}
      
      {/* Area Map */}
      {data.area_map && (
        <a href={data.area_map} target="_blank" rel="noopener noreferrer" className="map-link">
          🗺️ View All Hotels on Map
        </a>
      )}
    </div>
  );
};

// Booking Confirmation Component
const BookingConfirmation = ({ data }) => {
  const { booking, message, next_steps } = data;
  
  return (
    <div className="booking-simulation">
      <div className="booking-header">
        🎉 {message}
      </div>
      
      <div className="booking-details">
        <div><strong>Booking ID:</strong> <span className="booking-id">{booking.booking_id}</span></div>
        <div><strong>Type:</strong> {booking.type.toUpperCase()}</div>
        <div><strong>Status:</strong> <span style={{color: '#4caf50', fontWeight: 'bold'}}>{booking.status}</span></div>
        
        {booking.type === 'flight' && (
          <>
            <div><strong>Seat:</strong> {booking.seat_selection?.[0]?.seat} ({booking.seat_selection?.[0]?.type})</div>
            <div><strong>Baggage:</strong> {booking.extras?.baggage}</div>
          </>
        )}
        
        {booking.type === 'hotel' && (
          <>
            <div><strong>Room:</strong> {booking.room_type}</div>
            <div><strong>Breakfast:</strong> {booking.extras?.breakfast}</div>
          </>
        )}
        
        <div><strong>Amount Paid:</strong> ₹{booking.payment.amount.toLocaleString()}</div>
        <div><strong>Transaction ID:</strong> {booking.payment.transaction_id}</div>
      </div>
      
      {next_steps && (
        <div style={{marginTop: '15px'}}>
          <strong>Next Steps:</strong>
          <ul style={{marginTop: '5px', paddingLeft: '20px'}}>
            {next_steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="booking-actions">
        {booking.boarding_pass && (
          <a href={booking.boarding_pass} target="_blank" rel="noopener noreferrer" className="booking-btn">
            📱 Boarding Pass
          </a>
        )}
        {booking.voucher && (
          <a href={booking.voucher} target="_blank" rel="noopener noreferrer" className="booking-btn">
            📄 Voucher
          </a>
        )}
        {booking.manage_booking && (
          <a href={booking.manage_booking} target="_blank" rel="noopener noreferrer" className="booking-btn">
            ⚙️ Manage Booking
          </a>
        )}
      </div>
    </div>
  );
};

// User Preferences Component
const UserPreferences = ({ data }) => {
  const { user_profile, message } = data;
  const prefs = user_profile.preferences;
  
  return (
    <div className="preferences-panel">
      <h4>👤 {message}</h4>
      
      <div className="preference-item">
        <span className="preference-label">Seat Class:</span>
        <span className="preference-value">{prefs.seat_class}</span>
      </div>
      
      <div className="preference-item">
        <span className="preference-label">Hotel Star Rating:</span>
        <span className="preference-value">{'⭐'.repeat(prefs.hotel_star_rating)}</span>
      </div>
      
      <div className="preference-item">
        <span className="preference-label">Budget per Night:</span>
        <span className="preference-value">₹{prefs.budget_per_night.toLocaleString()}</span>
      </div>
      
      <div className="preference-item">
        <span className="preference-label">Max Layovers:</span>
        <span className="preference-value">{prefs.max_layovers}</span>
      </div>
      
      {prefs.price_alert_enabled && (
        <div className="price-alert" style={{marginTop: '10px'}}>
          🔔 Price alerts enabled ({prefs.price_alert_threshold}% threshold)
        </div>
      )}
    </div>
  );
};

export default EnhancedMessageRenderer;
