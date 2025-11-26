import React, { useEffect, useState } from 'react';
import { getDailyConsumption } from '../services/api';

function EnergyChart({ deviceId, date }) {
  const [data, setData] = useState([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!deviceId || !date) return;
    (async () => {
      try {
        const resp = await getDailyConsumption(deviceId, date);
        setData(resp.data.hourly_data);
        setErr('');
      } catch (e) {
        setErr('Failed to load consumption');
      }
    })();
  }, [deviceId, date]);

  const maxKwh = Math.max(...data.map(h => h.total_kwh), 1);
  const localOffset = new Date().getTimezoneOffset() / -60; 
  
  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Hourly Consumption ({date})</h3>
      {err && <p style={{ color: 'red' }}>{err}</p>}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        alignItems: 'flex-end',
        height: '250px',
        border: '1px solid #ddd',
        padding: '20px',
        backgroundColor: '#f9f9f9',
        position: 'relative'
      }}>
        {}
        <div style={{
          position: 'absolute',
          left: '5px',
          top: '10px',
          fontSize: '12px',
          color: '#666',
          writingMode: 'vertical-rl',
          transform: 'rotate(180deg)'
        }}>
          kWh
        </div>
        
        {data.map(h => {
          const heightPercent = (h.total_kwh / maxKwh) * 100;
          const barHeight = Math.max(heightPercent * 2, 5); 
          const localHour = (h.hour + localOffset + 24) % 24; 
          
          return (
            <div key={h.hour} style={{ 
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-end'
            }}>
              {}
              {h.total_kwh > 0 && (
                <div style={{
                  fontSize: '10px',
                  color: '#333',
                  marginBottom: '2px',
                  fontWeight: 'bold'
                }}>
                  {h.total_kwh.toFixed(2)}
                </div>
              )}
              
              {}
              <div style={{
                width: '100%',
                maxWidth: '30px',
                height: `${barHeight}px`,
                backgroundColor: h.total_kwh > 0 ? '#007bff' : '#e0e0e0',
                borderRadius: '4px 4px 0 0',
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }} 
              title={`${localHour}:00 local (${h.hour}:00 UTC): ${h.total_kwh} kWh`}
              />
              
              {}
              <small style={{ 
                marginTop: '5px',
                fontSize: '11px',
                color: '#666',
                fontWeight: h.hour === new Date().getUTCHours() ? 'bold' : 'normal'
              }}>
                {localHour}h
              </small>
            </div>
          );
        })}
      </div>
      
      {}
      <div style={{ 
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#e3f2fd',
        borderRadius: '4px',
        textAlign: 'center'
      }}>
        <strong>Total Daily Consumption: </strong>
        {data.reduce((sum, h) => sum + h.total_kwh, 0).toFixed(2)} kWh
      </div>
      
      {}
      <p style={{ 
        fontSize: '12px', 
        color: '#666', 
        marginTop: '10px',
        fontStyle: 'italic'
      }}>
        * Shown in local time (UTC{localOffset >= 0 ? '+' : ''}{localOffset})
      </p>
    </div>
  );
}

export default EnergyChart;