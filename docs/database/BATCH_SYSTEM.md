# Gemini API Batch Mode for Franchise Data Processing

This implementation adds **Gemini API Batch Mode** support to your franchise data processing pipeline, providing **50% cost savings** compared to sequential API calls.

## 🎯 Benefits

- **💰 50% Cost Savings**: Batch API calls are half the price of synchronous calls
- **⚡ Higher Throughput**: Increased rate limits for batch processing
- **🔄 Simplified Processing**: No need for complex retry logic
- **📈 Better Scalability**: Process hundreds of files efficiently

## 📁 New Files Created

```
src/api/genai_gemini_batch.py          # Batch mode utilities
src/data/nlp/genai_data_batch.py       # Batch data extraction
src/data/nlp/genai_keywords_batch.py   # Batch keyword extraction
src/data/nlp/batch_manager.py          # Pipeline orchestration
batch_cli.py                           # Command-line interface
```

## 🚀 Quick Start

### 1. Run the Complete Pipeline

```bash
# Submit both data extraction and keyword extraction jobs
python batch_cli.py pipeline

# Run pipeline and wait for completion (synchronous)
python batch_cli.py pipeline --wait
```

### 2. Run Individual Steps

```bash
# Extract franchise data from HTML files
python batch_cli.py data

# Extract keywords from franchise JSON files
python batch_cli.py keywords
```

### 3. Monitor Progress

```bash
# Check status of all batch jobs
python batch_cli.py status

# Estimate cost savings
python batch_cli.py estimate
```

## 📊 Usage Examples

### Example 1: Complete Pipeline

```bash
$ python batch_cli.py pipeline
🚀 Starting full franchise data processing pipeline in batch mode
💰 This will save 50% on API costs compared to sequential processing!
📄 Step 1: Submitting franchise data extraction batch job...
✅ Data extraction job submitted: projects/123/locations/us-central1/batchPredictionJobs/456
🔑 Step 2: Submitting keyword extraction batch job...
✅ Keywords extraction job submitted: projects/123/locations/us-central1/batchPredictionJobs/789
🎉 Batch pipeline submission completed!
```

### Example 2: Check Status

```bash
$ python batch_cli.py status
📊 Batch Job Status Report:
==================================================
✅ data_extraction_50_files
   ID: projects/123/locations/us-central1/batchPredictionJobs/456
   Type: data_extraction
   Status: completed
   Elapsed: 2.3 hours

⏳ keywords_extraction_50_files
   ID: projects/123/locations/us-central1/batchPredictionJobs/789
   Type: keywords_extraction
   Status: in_progress
   Elapsed: 1.8 hours
```

## 🔧 Advanced Usage

### Python API

```python
from src.data.nlp.batch_manager import (
    run_full_pipeline_batch,
    check_pipeline_status,
    estimate_cost_savings
)

# Submit pipeline jobs
jobs = run_full_pipeline_batch(wait_for_completion=False)

# Check status programmatically
check_pipeline_status()

# Get cost savings estimate
estimate_cost_savings()
```

### Individual Modules

```python
# Data extraction batch
from src.data.nlp.genai_data_batch import main_batch_async, check_batch_results

job_id = main_batch_async()  # Submit job
results = check_batch_results(job_id)  # Check results

# Keywords extraction batch
from src.data.nlp.genai_keywords_batch import main_batch_async, check_keywords_batch_results

job_id = main_batch_async()  # Submit job
results = check_keywords_batch_results(job_id)  # Check results
```

## ⚙️ Configuration

### Batch Job Settings

You can customize batch processing behavior:

```python
# In batch_manager.py or your scripts
run_full_pipeline_batch(
    wait_for_completion=True,    # Wait for each job to complete
    poll_interval=300           # Check status every 5 minutes
)
```

### Model Configuration

Batch mode uses simplified configurations:

- **Data Extraction**: `gemini-2.5-flash-lite` with structured output
- **Keywords Extraction**: `gemini-2.5-flash` (simplified, no tools/thinking)

## 🚨 Important Notes

### Limitations in Batch Mode

1. **No Tools Support**: Google Search and URL Context tools are not available in batch mode
2. **No Thinking Config**: Advanced reasoning features are disabled
3. **Processing Time**: Jobs complete within 24 hours (usually much faster)
4. **File Size Limits**: Individual requests must fit within token limits

### Fallback Strategy

If you need the advanced features (tools, thinking), you can still use the original sequential processing:

```python
# Original sequential processing (with all features)
from src.data.nlp.genai_data import main as data_main
from src.data.nlp.genai_keywords import main as keywords_main

data_main()      # Sequential data extraction
keywords_main()  # Sequential keyword extraction
```

## 📈 Cost Comparison

| Processing Mode | Cost    | Features                       | Processing Time |
| --------------- | ------- | ------------------------------ | --------------- |
| Sequential      | 100%    | All features (tools, thinking) | Real-time       |
| Batch           | **50%** | Core features only             | Up to 24 hours  |

### When to Use Batch Mode

✅ **Use Batch Mode When:**

- Processing large datasets (50+ files)
- Cost optimization is important
- Processing time is not critical
- You don't need Google Search or advanced reasoning

❌ **Use Sequential Mode When:**

- You need immediate results
- Google Search integration is required
- Advanced thinking/reasoning is needed
- Processing small datasets (< 10 files)

## 🔍 Monitoring and Debugging

### Check Job Progress

```bash
# Get detailed status
python batch_cli.py status

# Wait for specific job
python batch_cli.py wait JOB_ID data
```

### Debug Failed Jobs

Batch results and logs are saved in:

```
data/raw/batch_results/
├── franchise_data/
│   ├── job_name_requests.jsonl    # Original requests
│   └── job_name_results.jsonl     # API responses
├── keywords/
│   ├── job_name_requests.jsonl
│   └── job_name_results.jsonl
└── batch_jobs.json                # Job tracking
```

### Common Issues

1. **"No files found"**: Ensure HTML files are in `data/external/` for data extraction
2. **"Batch job failed"**: Check API quotas and file formatting
3. **"JSON decode error"**: Batch responses may need different parsing

## 🔄 Migration Guide

### From Sequential to Batch

Replace your current processing:

```python
# OLD: Sequential processing
from src.data.nlp.genai_data import main as data_main
from src.data.nlp.genai_keywords import main as keywords_main

data_main()
keywords_main()
```

```python
# NEW: Batch processing
from src.data.nlp.batch_manager import run_full_pipeline_batch

jobs = run_full_pipeline_batch()
```

### Hybrid Approach

Use batch for bulk processing, sequential for individual files:

```python
# Batch process existing files
run_full_pipeline_batch()

# Process new files sequentially as they arrive
# (use original sequential functions)
```

## 🎓 Examples by Use Case

### Large Dataset Processing

```bash
# Process 100+ franchise files
python batch_cli.py estimate  # Check savings first
python batch_cli.py pipeline  # Submit jobs
python batch_cli.py status    # Monitor progress
```

### Development Testing

```bash
# Test with smaller batches
python batch_cli.py data      # Test data extraction only
python batch_cli.py status    # Check results
python batch_cli.py keywords  # Test keyword extraction
```

### Production Deployment

```python
# Automated batch processing
import schedule
import time

def run_daily_batch():
    run_full_pipeline_batch(wait_for_completion=False)

schedule.every().day.at("02:00").do(run_daily_batch)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## 📞 Support

If you encounter issues:

1. Check the status with `python batch_cli.py status`
2. Review batch result files in `data/raw/batch_results/`
3. For urgent processing, use the original sequential mode
4. Check Gemini API quotas and limits

---

**🎉 Happy batch processing with 50% cost savings!**
