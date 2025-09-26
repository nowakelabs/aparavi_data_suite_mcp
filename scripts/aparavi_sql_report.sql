-- Complete buffer pool and transaction durability health check with performance guidance
-- This query provides comprehensive overview of buffer pool configuration, performance, and durability settings

SELECT 
  'Configuration' AS section,
  'Buffer Pool Size' AS metric,
  CONCAT(ROUND(@@innodb_buffer_pool_size/1024/1024/1024, 2), ' GB') AS value
  -- IDEAL: 70-80% of total system RAM on dedicated DB servers
  -- This is the total memory allocated for caching InnoDB data and indexes

UNION ALL
SELECT 'Configuration', 'Instances', @@innodb_buffer_pool_instances
  -- IDEAL: 8 for most systems, up to 64 for very large buffer pools (>32GB)
  -- Multiple instances reduce mutex contention in high-concurrency workloads
  -- Each instance should be at least 1GB for optimal performance
objects
UNION ALL
SELECT 'Configuration', 'Size Per Instance', CONCAT(ROUND(@@innodb_buffer_pool_size/@@innodb_buffer_pool_instances/1024/1024/1024, 2), ' GB')
  -- IDEAL: >= 1GB per instance (required by MySQL for efficiency)
  -- If this shows < 1GB, reduce the number of instances
  -- Formula: buffer_pool_size / instances should be >= 1GB

UNION ALL
SELECT 'Configuration', 'Log Flush at Commit', @@innodb_flush_log_at_trx_commit
  -- CRITICAL DURABILITY vs PERFORMANCE SETTING:
  -- 0 = Fastest, least durable (can lose ~1 sec of data on any crash)
  -- 1 = Slowest, fully ACID compliant (no data loss, recommended for critical data)
  -- 2 = Balanced (no data loss on MySQL crash, ~1 sec loss on OS/hardware crash)

UNION ALL
SELECT 'Usage', 'Data Pages', CONCAT(ROUND((SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_pages_data') * 16384 / 1024 / 1024 / 1024, 2), ' GB')
  -- This shows how much buffer pool space is actually occupied by cached data
  -- Compare with "Buffer Pool Size" to see how much capacity you're using
  -- If consistently much lower than total size, you may have over-allocated

UNION ALL
SELECT 'Usage', 'Utilization %', CONCAT(ROUND((SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_pages_data') * 100.0 / (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_pages_total'), 2), '%')
  -- IDEAL: 70-95% for well-tuned systems under normal load
  -- < 70%: Buffer pool may be oversized, or system is lightly loaded
  -- > 95%: Buffer pool may be undersized, monitor for performance issues
  -- This metric shows how efficiently you're using allocated buffer pool memory

UNION ALL
SELECT 'Performance', 'Hit Ratio %', CONCAT(ROUND(100 - ((SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_reads') * 100.0 / (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_read_requests')), 4), '%')
  -- IDEAL: > 99% (higher is better, 99.9%+ is excellent)
  -- This shows how often data requests are served from memory vs. disk
  -- < 99%: Indicates significant disk I/O - consider increasing buffer pool size
  -- < 95%: Poor performance, buffer pool definitely too small for working set
  -- This is the most critical performance metric for buffer pool efficiency

ORDER BY section, metric;

/*
INTERPRETATION GUIDE:
===================

CONFIGURATION HEALTH:
- Buffer Pool Size: Should be 70-80% of system RAM on dedicated servers
- Instances: Start with 8, increase for buffer pools > 8GB if seeing contention
- Size Per Instance: Must be >= 1GB, if not, reduce instance count
- Log Flush at Commit: Critical durability vs performance tradeoff (see details below)

USAGE PATTERNS:
- Data Pages: Shows actual memory used for caching data
- Utilization %: 70-95% indicates good sizing, outside this range suggests tuning needed

PERFORMANCE INDICATORS:
- Hit Ratio: > 99% is good, > 99.9% is excellent
- If hit ratio is low, either increase buffer pool size or optimize queries

innodb_flush_log_at_trx_commit DETAILED EXPLANATION:
================================================

VALUE 0 (Performance Mode):
- Behavior: Log buffer written to log file and flushed to disk once per second
- Performance: FASTEST - minimal I/O overhead per transaction
- Durability: WEAKEST - can lose up to 1 second of committed transactions on ANY crash
- Use Case: High-performance applications where some data loss is acceptable
- Risk: MySQL crash, OS crash, or power failure can lose recent transactions

VALUE 1 (ACID Compliance - Default):
- Behavior: Log buffer written and flushed to disk at EVERY transaction commit
- Performance: SLOWEST - significant I/O overhead per transaction
- Durability: STRONGEST - full ACID compliance, no data loss
- Use Case: Financial systems, critical data where no loss is acceptable
- Risk: None - fully durable but impacts performance on high-transaction workloads

VALUE 2 (Balanced Mode):
- Behavior: Log buffer written to OS at every commit, flushed to disk once per second
- Performance: MODERATE - better than 1, slower than 0
- Durability: MODERATE - survives MySQL crashes, can lose ~1 sec on OS/hardware crash
- Use Case: Most production systems - good balance of performance and durability
- Risk: OS crash or power failure can lose up to 1 second of transactions

RECOMMENDED SETTINGS BY USE CASE:
- Financial/Critical Systems: Use 1 (full durability)
- General Production: Use 2 (balanced - most common choice)
- Development/Testing: Use 0 or 2 (performance focused)
- High-Volume OLTP: Consider 2 with good UPS/hardware
- Read-Heavy Workloads: Setting has minimal impact

RED FLAGS:
- Size Per Instance < 1GB: Reduce instances
- Hit Ratio < 99%: Increase buffer pool size (if you have available RAM)
- Utilization consistently < 50%: Buffer pool may be oversized
- Utilization consistently > 95% with low hit ratio: Increase buffer pool size
- flush_log_at_trx_commit = 0 in production: Evaluate if data loss risk is acceptable

MONITORING FREQUENCY:
- Check daily during performance optimization
- Monitor hit ratio continuously in production
- Review configuration quarterly or after workload changes
- Audit durability settings during security/compliance reviews
*/