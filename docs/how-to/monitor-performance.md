# Monitor Performance

This guide covers how to monitor and optimize the performance of aider-lint-fixer.

## Performance Monitoring

### Basic Performance Metrics

```bash
# Run with timing information
python -m aider_lint_fixer --profile --output-stats

# Memory usage monitoring
python -m memory_profiler aider_lint_fixer/main.py
```

### Built-in Monitoring

```python
# Enable performance monitoring
export PERFORMANCE_MONITORING=true
export LOG_LEVEL=DEBUG

python -m aider_lint_fixer --monitor-performance
```

## Key Performance Indicators (KPIs)

### Processing Speed
- Files processed per minute
- Lines of code analyzed per second
- Time to first lint result

### Resource Usage
- Memory consumption
- CPU utilization
- Disk I/O patterns

### Quality Metrics
- Issues detected per file
- False positive rate
- Fix success rate

## Performance Profiling

### CPU Profiling

```bash
# Profile CPU usage
python -m cProfile -o profile.stats -m aider_lint_fixer

# Analyze profile data
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler psutil

# Profile memory usage
python -m memory_profiler aider_lint_fixer/main.py

# Line-by-line memory profiling
@profile
def analyze_file(filepath):
    # Function implementation
    pass
```

### I/O Profiling

```bash
# Monitor file I/O
python -m aider_lint_fixer --io-profile

# Use iotop for system-wide I/O monitoring
sudo iotop -p $(pgrep -f aider_lint_fixer)
```

## Performance Optimization

### Configuration Tuning

```yaml
# config/performance.yml
performance:
  max_workers: 4          # Parallel processing
  chunk_size: 100         # Files per batch
  cache_size: 1000        # Result cache size
  timeout: 30             # Operation timeout
  
optimization:
  enable_caching: true
  use_incremental: true   # Only process changed files
  skip_large_files: true  # Skip files > 1MB
```

### Parallel Processing

```python
# Enable parallel processing
python -m aider_lint_fixer --workers 4 --parallel

# Fine-tune worker count
import multiprocessing
optimal_workers = multiprocessing.cpu_count() - 1
```

### Caching Strategies

```bash
# Enable result caching
export ENABLE_CACHE=true
export CACHE_DIR=~/.cache/aider-lint-fixer

# Clear cache when needed
python -m aider_lint_fixer --clear-cache
```

## Monitoring Tools

### System Monitoring

```bash
# htop for real-time monitoring
htop -p $(pgrep -f aider_lint_fixer)

# iostat for I/O statistics
iostat -x 1

# vmstat for memory statistics
vmstat 1
```

### Application Monitoring

```python
# Custom performance monitoring
import time
import psutil
import logging

def monitor_performance():
    process = psutil.Process()
    
    while True:
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        logging.info(f"CPU: {cpu_percent}%, Memory: {memory_mb}MB")
        time.sleep(60)
```

### Cloud Monitoring

```yaml
# CloudWatch (AWS)
cloudwatch:
  metrics:
    - name: ProcessingTime
      unit: Seconds
    - name: MemoryUsage
      unit: Bytes
    - name: ErrorRate
      unit: Percent

# Application Insights (Azure)
appinsights:
  instrumentation_key: your_key
  track_dependencies: true
  track_requests: true
```

## Performance Benchmarking

### Baseline Measurements

```bash
# Create performance baseline
python scripts/benchmark.py --baseline --output baseline.json

# Compare current performance
python scripts/benchmark.py --compare baseline.json
```

### Load Testing

```bash
# Test with large codebases
python -m aider_lint_fixer --test-performance \
  --large-files 1000 \
  --max-filesize 10MB

# Stress testing
python scripts/stress_test.py --duration 300 --concurrent 10
```

### Regression Testing

```python
# Performance regression tests
def test_performance_regression():
    start_time = time.time()
    
    # Run linting operation
    result = lint_large_codebase()
    
    duration = time.time() - start_time
    assert duration < PERFORMANCE_THRESHOLD
```

## Performance Alerts

### Threshold-Based Alerts

```yaml
# alerts.yml
alerts:
  high_memory_usage:
    threshold: 1GB
    action: log_warning
    
  slow_processing:
    threshold: 5min
    action: send_notification
    
  high_error_rate:
    threshold: 10%
    action: stop_processing
```

### Automated Monitoring

```python
# Performance monitoring script
import psutil
import time
import smtplib

def check_performance():
    process = get_aider_process()
    
    if process.memory_percent() > 80:
        send_alert("High memory usage detected")
    
    if get_processing_time() > 300:
        send_alert("Processing taking too long")
```

## Performance Reporting

### Daily Reports

```bash
# Generate daily performance report
python scripts/generate_report.py --daily --format html

# Key metrics to include:
# - Average processing time
# - Peak memory usage
# - Files processed
# - Error rates
```

### Performance Dashboard

```python
# Simple dashboard with matplotlib
import matplotlib.pyplot as plt
import pandas as pd

def create_performance_dashboard():
    df = load_performance_data()
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Processing time trend
    axes[0,0].plot(df['timestamp'], df['processing_time'])
    axes[0,0].set_title('Processing Time Trend')
    
    # Memory usage
    axes[0,1].plot(df['timestamp'], df['memory_usage'])
    axes[0,1].set_title('Memory Usage')
    
    # Throughput
    axes[1,0].bar(df['hour'], df['files_processed'])
    axes[1,0].set_title('Files Processed per Hour')
    
    # Error rate
    axes[1,1].plot(df['timestamp'], df['error_rate'])
    axes[1,1].set_title('Error Rate')
    
    plt.tight_layout()
    plt.savefig('performance_dashboard.png')
```

## Troubleshooting Performance Issues

### Common Performance Problems

1. **High Memory Usage**
   - Reduce batch size
   - Enable garbage collection
   - Use streaming for large files

2. **Slow Processing**
   - Increase parallel workers
   - Enable caching
   - Skip unnecessary checks

3. **High CPU Usage**
   - Optimize regex patterns
   - Reduce worker count
   - Use more efficient algorithms

### Diagnostic Commands

```bash
# Memory leaks
python -m aider_lint_fixer --debug-memory

# CPU bottlenecks
python -m aider_lint_fixer --profile-cpu

# I/O issues
python -m aider_lint_fixer --trace-io
```

## Performance Best Practices

### Development
- Profile code regularly
- Use efficient data structures
- Minimize I/O operations
- Cache expensive computations

### Deployment
- Right-size compute resources
- Use SSD storage for better I/O
- Monitor resource utilization
- Set up automated scaling

### Maintenance
- Regular performance testing
- Update dependencies
- Clean up cache files
- Review configuration settings

## Next Steps

- [Security Best Practices](./security-best-practices.md)
- [Integrate with Aider](./integrate-with-aider.md)
- [Setup Development Environment](./setup-development-environment.md)
