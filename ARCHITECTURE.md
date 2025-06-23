# LLMS File Builder - Architecture Guide

## System Architecture Overview

The LLMS File Builder follows a **modular pipeline architecture** with clear separation of concerns and extensibility in mind.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Input Layer   │     │ Processing Core │     │  Output Layer   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ • CSV Files     │ --> │ • Validation    │ --> │ • LLMS.txt      │
│ • User Config   │     │ • Filtering     │     │ • LLMS.json     │
│ • API Keys      │     │ • Categorization│     │ • Preview       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Core Components Deep Dive

### 1. CSV Processor (`backend/csv_processor.py`)

**Purpose**: Handles all CSV-related operations with a focus on data quality and robustness.

```python
class CSVProcessor:
    """
    Responsibilities:
    - File validation and encoding detection
    - Column verification and mapping
    - Content filtering (remove non-HTML)
    - Deduplication logic
    - Quality analysis and scoring
    """
```

**Key Design Decisions**:

- **Lazy Loading**: Uses pandas chunking for large files (>200MB)
- **Encoding Detection**: Tries UTF-8 first, falls back to Latin-1
- **Smart Deduplication**: Prioritizes service pages over location pages when titles conflict

**Data Flow**:
```
Raw CSV → Validation → Filtering → Deduplication → Clean DataFrame
```

### 2. Categorizer (`backend/categorizer.py`)

**Purpose**: Intelligent page grouping using dual-strategy approach.

```python
class Categorizer:
    """
    Two-phase approach:
    1. Pattern-based categorization (primary)
    2. GPT enhancement for descriptions (optional)
    """
```

**Pattern Matching Strategy**:

```python
# Priority order for URL pattern matching
1. URL structure (/services/, /blog/, etc.)
2. URL segments (split by /, -, _)
3. Title content
4. Meta description content
5. H1 content

# Scoring algorithm
- URL match: 3 points
- Title match: 2 points
- Content match: 1 point
```

**GPT Enhancement Architecture**:

```
Pages → Batch (10) → GPT Prompt → Enhanced Descriptions → Merge
         ↓                ↓                                  ↓
      Token Count    Rate Limiting                    Validation
```

### 3. LLMS Generator (`backend/llms_generator.py`)

**Purpose**: Creates standardized output files with validation.

**Output Pipeline**:
```
Categorized Data → Template Engine → Validation → File Writing
                        ↓
                   Format Rules:
                   - Markdown syntax
                   - Link validation
                   - UTF-8 encoding
```

### 4. Orchestrator (`backend/llms_processor.py`)

**Purpose**: Coordinates the entire pipeline and manages state.

```python
class LLMSProcessor:
    """
    Pipeline stages:
    1. Initialize components
    2. Validate inputs
    3. Process CSV
    4. Categorize pages
    5. Generate outputs
    6. Handle errors
    """
```

## Data Models

### Page Data Structure

```python
Page = {
    "url": str,           # Normalized URL
    "title": str,         # From Title 1 or extracted from URL
    "description": str,   # Meta or enhanced description
    "category": str,      # Assigned category
    "priority": float,    # For deduplication
}
```

### Site Metadata

```python
SiteMetadata = {
    "site_title": str,    # From homepage title
    "site_summary": str,  # From homepage meta
    "site_url": str,      # Base URL
}
```

### Processing Stats

```python
Stats = {
    "total_rows": int,
    "indexable_pages": int,
    "unique_pages": int,
    "quality_score": float,
    "processing_time": float,
}
```

## Design Patterns

### 1. **Builder Pattern** - LLMS Generator

```python
generator = LLMSGenerator()
    .set_metadata(site_metadata)
    .add_sections(categorized_pages)
    .configure_format(include_stats=True)
    .build()
```

### 2. **Strategy Pattern** - Categorization

```python
# Interchangeable categorization strategies
if use_gpt:
    strategy = GPTEnhancedStrategy()
else:
    strategy = PatternBasedStrategy()

categorizer.set_strategy(strategy)
```

### 3. **Pipeline Pattern** - Processing Flow

```python
pipeline = ProcessingPipeline()
    .add_stage(ValidationStage())
    .add_stage(FilteringStage())
    .add_stage(CategorizationStage())
    .add_stage(OutputStage())
    .execute(input_data)
```

## Performance Considerations

### Memory Management

- **Streaming**: Large CSV files processed in chunks
- **Garbage Collection**: Explicit cleanup after processing stages
- **Data Structures**: Using sets for O(1) duplicate checking

### API Rate Limiting

```python
# GPT API throttling
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 0.5  # seconds
MAX_RETRIES = 3
```

### Optimization Techniques

1. **URL Normalization Cache**
   ```python
   @lru_cache(maxsize=10000)
   def normalize_url(url: str) -> str:
       return url.rstrip('/').lower()
   ```

2. **Compiled Regex Patterns**
   ```python
   # Pre-compile frequently used patterns
   IMAGE_PATTERN = re.compile(r'\.(jpg|jpeg|png|gif|webp)$', re.I)
   ```

3. **Vectorized Operations**
   ```python
   # Use pandas vectorized operations
   df['is_image'] = df['url'].str.contains(IMAGE_PATTERN)
   ```

## Error Handling Strategy

### Hierarchical Error Handling

```
Application Level
    ↓
Component Level
    ↓
Operation Level
```

### Error Categories

1. **Recoverable Errors**
   - API timeouts → Retry with backoff
   - Encoding issues → Try alternative encoding
   - Missing optional data → Use defaults

2. **Non-Recoverable Errors**
   - Missing required columns → Fail with guidance
   - Invalid file format → Fail with instructions
   - No API key for GPT mode → Fail with setup help

## Extension Points

### Adding New Categories

```python
# 1. Define patterns in config
NEW_PATTERNS = {
    "Products": ["product", "item", "sku"],
    "Support": ["help", "faq", "guide"]
}

# 2. Register with categorizer
categorizer.update_patterns(NEW_PATTERNS)
```

### Custom Output Formats

```python
# Implement new generator
class XMLGenerator(BaseGenerator):
    def generate(self, data):
        # Custom XML generation logic
        pass

# Register generator
output_generators['xml'] = XMLGenerator()
```

### Industry-Specific Adaptations

```python
# Medical industry adapter
class MedicalAdapter:
    def enhance_patterns(self):
        return {
            "Procedures": ["surgery", "operation"],
            "Conditions": ["diagnosis", "symptoms"],
        }
    
    def validate_compliance(self, content):
        # HIPAA compliance checks
        pass
```

## Testing Architecture

### Test Pyramid

```
         E2E Tests
        /    |    \
    Integration Tests
   /    |    |    |   \
Unit Tests (Most tests)
```

### Test Data Management

```python
# Test fixtures
fixtures/
├── minimal_valid.csv      # Minimum viable CSV
├── large_dataset.csv      # Performance testing
├── edge_cases.csv         # Unusual data
└── multilingual.csv       # i18n testing
```

## Security Considerations

### API Key Management

```python
# Never store keys in code
api_key = os.getenv("OPENAI_API_KEY")

# Validate key format
if not api_key.startswith("sk-"):
    raise ValueError("Invalid API key format")
```

### Input Sanitization

```python
# Prevent path traversal
safe_filename = Path(user_input).name

# URL validation
parsed = urlparse(url)
if parsed.scheme not in ['http', 'https']:
    raise ValueError("Invalid URL scheme")
```

## Monitoring and Logging

### Structured Logging

```python
logger.info("Processing started", extra={
    "csv_size": file_size,
    "use_gpt": use_gpt,
    "timestamp": datetime.now()
})
```

### Performance Metrics

```python
metrics = {
    "processing_time": timer.elapsed(),
    "pages_per_second": pages_count / timer.elapsed(),
    "gpt_calls": gpt_counter,
    "memory_peak": resource.getrusage().ru_maxrss
}
```

## Future Architecture Considerations

### Microservices Migration

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ CSV Service │     │ Categorizer │     │  Generator  │
│   (API)     │────▶│   Service   │────▶│   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ GPT Service │
                    └─────────────┘
```

### Scalability Path

1. **Horizontal Scaling**: Process multiple CSVs in parallel
2. **Caching Layer**: Redis for processed results
3. **Queue System**: Celery for async processing
4. **API Gateway**: REST API for integrations

## Development Workflow

### Local Development

```bash
# Set up pre-commit hooks
pre-commit install

# Run tests with coverage
pytest --cov=backend tests/

# Profile performance
python -m cProfile -o profile.stats run.py large_file.csv
```

### Code Quality Standards

- Type hints for all public methods
- Docstrings following Google style
- Maximum complexity: 10 (McCabe)
- Test coverage: >80%

---

This architecture is designed to be **maintainable**, **extensible**, and **performant** while solving the specific problem of converting SEO crawl data into AI-optimized content discovery files.