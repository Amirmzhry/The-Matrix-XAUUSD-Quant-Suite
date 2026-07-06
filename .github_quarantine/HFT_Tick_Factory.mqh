#property strict

class CTickFactory {
private:
    int m_window;
    int m_half_window;
    double m_k_sigma;
    double m_buffer[];
    double m_sorted_buffer[];
    double m_deviations[];
    int m_count;
    int m_index;
    bool m_is_ready;

public:
    CTickFactory(int half_window_param = 11, double k_sigma_param = 1.95) {
        m_half_window = half_window_param;
        m_window = 23;
        m_k_sigma = k_sigma_param;
        m_count = 0; m_index = 0; m_is_ready = false;
        
        ArrayResize(m_buffer, m_window); 
        ArrayResize(m_sorted_buffer, m_window);
        ArrayResize(m_deviations, m_window);
        ArrayInitialize(m_buffer, 0.0);
        ArrayInitialize(m_sorted_buffer, 0.0);
        ArrayInitialize(m_deviations, 0.0);
    }
    
    ~CTickFactory() { 
        ArrayFree(m_buffer); 
        ArrayFree(m_sorted_buffer);
        ArrayFree(m_deviations); 
    }

    bool UpdateTick(double current_bid, double current_ask, double &filtered_bid, double &filtered_ask) {
        double raw_spread = current_ask - current_bid;
        double mid_price = (current_bid + current_ask) / 2.0;
        
        m_buffer[m_index] = mid_price;
        m_index = (m_index + 1) % m_window;
        
        if (!m_is_ready) {
            m_count++;
            if (m_count >= m_window) { m_is_ready = true; }
            filtered_bid = current_bid;
            filtered_ask = current_ask;
            return true;
        }
        
        ArrayCopy(m_sorted_buffer, m_buffer); 
        ArraySort(m_sorted_buffer);
        double median = m_sorted_buffer[m_window / 2];
        
        for (int i = 0; i < m_window; i++) {
            m_deviations[i] = MathAbs(m_buffer[i] - median);
        }
        ArraySort(m_deviations);
        
        double mad_value = m_deviations[m_window / 2];
        double sigma = 1.4826 * mad_value;
        
        double filtered_mid = mid_price;
        if (MathAbs(mid_price - median) > (m_k_sigma * sigma)) {
            filtered_mid = median;
        }
        
        filtered_bid = filtered_mid - raw_spread / 2.0;
        filtered_ask = filtered_mid + raw_spread / 2.0;
        return true;
    }
};