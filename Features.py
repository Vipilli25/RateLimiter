import time
import statistics
import logging

# http://localhost:8000/weather?city=Pune

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_features(redis_client, user_key):
    def fetch_timestamps():
        timestamps_key = f"{user_key}:timestamps"
        timestamps = redis_client.lrange(timestamps_key, 0, -1)
        return sorted([float(ts) for ts in timestamps])

    def calculate_peak_request_rate(timestamps):
        peak_rate = 0
        start = 0
        for end in range(len(timestamps)):
            while timestamps[end] - timestamps[start] > 5:
                start += 1

            peak_rate = max(peak_rate, end - start + 1)
        return peak_rate

    def calculate_std_dev_gaps(timestamps):
        if len(timestamps) < 3:
            return 0.0  
        gaps = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        if len(gaps) < 2:
            return 0.0
        return statistics.stdev(gaps)


    def calculate_burst_features(timestamps, burst_threshold=5, burst_window=2):
        bursts = 0
        start = 0
        for end in range(len(timestamps)):
            while timestamps[end] - timestamps[start] > burst_window:
                start += 1
            burst_size = end - start + 1
            if burst_size > burst_threshold:
                bursts += 1
        return bursts

    def calculate_tokens_used_per_second(timestamps, current_time):
        if not timestamps:
            return 0.0
        first_request = timestamps[0]
        time_span = max(current_time - first_request, 1)
        return len(timestamps) / time_span

    timestamps = fetch_timestamps()
    if not timestamps:
        return None

    current_time = time.time()

    features = {
        "peak_request_rate": calculate_peak_request_rate(timestamps),
        "request_count_total": len(timestamps),
        "std_dev_gaps": calculate_std_dev_gaps(timestamps),
        "no_of_bursts": calculate_burst_features(timestamps),
        "tokens_used_per_second": calculate_tokens_used_per_second(timestamps, current_time),
    }

    return features

def label_fill_rate(features):
    """
    Assign fill rate using a weighted score of normalized feature values.
    More flexible and expressive than discrete rules.
    """

    # Normalized features (values between 0 and 1 or reasonable capped scales)
    peak = min(features["peak_request_rate"] / 20, 1.0)  # normalize for peak rates up to 20
    tups = min(features["tokens_used_per_second"] / 1.8, 1.0)  # assume 3 tps is extreme
    stddev = min(features["std_dev_gaps"] / 5, 1.0)  # assume 4s gap stdev is wild
    bursts = min(features["no_of_bursts"] / 10, 1.0)  # 10 bursts is upper cap

    w_peak = 2.0
    w_tups = 1.2
    w_stddev = -1.0  
    w_bursts = -2.0  

    # Weighted sum
    score = (
        w_peak * (1 - peak) +        
        w_tups * (1 - tups) +        
        w_stddev * stddev +          
        w_bursts * bursts           
    )

    fill_rate = round(max(1, min(5, 1 + score)))  

    return fill_rate



def log_features(redis_client, user_key, client_ip):
    features = extract_features(redis_client, user_key)
    if features is None:
        logging.warning(f"[{client_ip}] No timestamps found for user '{user_key}'.")
        return

    fill_rate = label_fill_rate(features)

    logging.info(f"[{client_ip}] Extracted Features for user '{user_key}':")
    for feature_name, value in features.items():
        logging.info(f"[{client_ip}] {feature_name}: {value}")

    logging.info(f"[{client_ip}] Heuristically Labeled Fill Rate: {fill_rate}")
