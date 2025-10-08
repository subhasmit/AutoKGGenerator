# Automated Knowledge Graph Generator

A comprehensive, production-ready system for converting unknown CSV, JSON, and text files into RDF knowledge graphs using LangChain, RDFLib, and OpenAI's Batch API with structured outputs.

## Features

### 🚀 **Automated Processing**
- **Automatic file type detection** for CSV, JSON, and text files
- **Schema inference** for structured data sources
- **Intelligent chunking** for large documents
- **Batch processing** with OpenAI API for cost efficiency (50% savings)

### 🧠 **LLM-Powered Extraction**
- **Structured outputs** using Pydantic models for reliable extraction
- **Entity recognition** for persons, organizations, locations, concepts, events, products
- **Relationship extraction** with confidence scoring
- **Ontology mapping** to standard vocabularies (FOAF, Schema.org, DBpedia)

### 📊 **RDF Generation**
- **Native RDF support** using RDFLib
- **Turtle format export** with proper namespace management
- **Provenance tracking** and metadata inclusion
- **Graph statistics** and validation

### 🔧 **Production Ready**
- **Comprehensive error handling** and logging
- **CLI interface** for easy deployment
- **Configurable processing** via YAML configuration
- **Extensible architecture** for custom ontologies

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd automated-kg-generator

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Usage

```bash
# Process all files in a directory
python automated_kg_generator.py --input-dir /path/to/data --output-file knowledge_graph.ttl
```

### Python API Usage

```python
from automated_kg_generator import AutomatedKGGenerator

# Initialize generator
generator = AutomatedKGGenerator(
    openai_api_key="your-api-key",
    base_namespace="http://your-domain.org/kg/"
)

# Generate knowledge graph
result = generator.generate_knowledge_graph(
    input_directory="/path/to/data",
    output_file="output.ttl"
)

print(f"Generated {result['statistics']['total_triples']} triples")
```

## Architecture

The system follows a layered architecture:

1. **Input Layer**: File detection and loading using LangChain document loaders
2. **Processing Layer**: Schema inference, content analysis, and chunking
3. **LLM Layer**: Batch processing with OpenAI API and structured outputs
4. **RDF Layer**: Triple generation and graph construction using RDFLib
5. **Output Layer**: Turtle export with statistics and metadata

## Configuration

Copy `config_example.yaml` to `config.yaml` and customize settings:

```yaml
# OpenAI Configuration
openai:
  model: "gpt-4o-2024-08-06"
  max_tokens: 4000
  temperature: 0.1

# RDF Configuration  
rdf:
  base_namespace: "http://example.org/kg/"
  output_format: "turtle"
  include_confidence_scores: true

# Processing Configuration
processing:
  chunk_size: 3000
  chunk_overlap: 200
  confidence_threshold: 0.5
```

## Supported Input Formats

### CSV Files
- Automatic column detection and type inference
- Relationship discovery between entities across rows
- Support for various encodings and delimiters

```csv
name,position,company,location
John Smith,Engineer,TechCorp,San Francisco
Jane Doe,Scientist,DataLab,New York
```

### JSON Files
- Hierarchical structure parsing
- Nested relationship extraction
- Support for JSON and JSONL formats

```json
{
  "companies": [
    {
      "name": "TechCorp",
      "founded": 2010,
      "employees": [{"name": "John Smith", "role": "Engineer"}]
    }
  ]
}
```

### Text Documents
- Natural language processing for entity extraction
- Relationship identification between entities
- Support for various text formats (.txt, .md)

```text
TechCorp announced a partnership with DataLab. 
John Smith, lead engineer at TechCorp, will oversee the collaboration.
```

## Output Format

The system generates RDF in Turtle format with proper namespaces:

```turtle
@prefix kg: <http://example.org/kg/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix schema: <http://schema.org/> .

kg:person_John_Smith a foaf:Person ;
    foaf:name "John Smith" ;
    schema:worksFor kg:organization_TechCorp ;
    kg:confidence 0.95 .

kg:organization_TechCorp a foaf:Organization ;
    schema:name "TechCorp" ;
    schema:foundingDate 2010 .
```

## Advanced Features

### Batch Processing with OpenAI API

The system leverages OpenAI's Batch API for efficient processing:

- **Cost Efficiency**: 50% discount compared to real-time API
- **Higher Limits**: Separate rate limit pool with significantly more capacity
- **Reliable Processing**: 24-hour completion guarantee
- **Scalable**: Up to 50,000 requests per batch

### Structured Outputs

Uses Pydantic models for reliable LLM output parsing:

```python
class ExtractedEntity(BaseModel):
    name: str
    type: EntityType
    properties: Dict[str, str]
    confidence: float

class KnowledgeExtractionResult(BaseModel):
    entities: List[ExtractedEntity] 
    relationships: List[ExtractedRelationship]
    metadata: Dict[str, Any]
```

### Ontology Integration

Supports mapping to standard vocabularies:

- **FOAF**: Friend of a Friend for person and organization data
- **Schema.org**: General-purpose structured data vocabulary
- **DBpedia**: Linking to Wikipedia concepts
- **Dublin Core Terms**: Metadata and provenance
- **Custom ontologies**: Extensible for domain-specific vocabularies

## CLI Options

```bash
python automated_kg_generator.py [OPTIONS]

Options:
  --input-dir PATH          Input directory [required]
  --output-file PATH        Output RDF file [default: knowledge_graph.ttl]
  --openai-api-key TEXT     OpenAI API key
  --base-namespace TEXT     Base RDF namespace
  --config PATH             Configuration file path
  --verbose                 Enable verbose logging
  --dry-run                 Show processing plan without execution
```

## Performance and Scalability

### Processing Capabilities
- **Large Files**: Automatic chunking for files > 3MB
- **Batch Processing**: Up to 50,000 documents per batch
- **Memory Efficient**: Streaming processing for large datasets
- **Parallel Processing**: Concurrent document loading and preprocessing

### Cost Optimization
- **Batch API**: 50% cost reduction vs real-time processing
- **Smart Chunking**: Optimal token usage
- **Caching**: Avoid reprocessing identical content
- **Incremental Updates**: Process only changed files

## Error Handling

Comprehensive error handling for production use:

- **File Format Errors**: Graceful handling of corrupted files
- **API Failures**: Retry logic with exponential backoff
- **Memory Issues**: Automatic chunk size adjustment
- **Validation Errors**: RDF graph validation and repair
- **Partial Failures**: Continue processing despite individual file errors

## Monitoring and Logging

Built-in monitoring capabilities:

```python
# Statistics tracking
stats = generator.get_statistics()
print(f"Entities extracted: {stats['entities']}")
print(f"Relationships found: {stats['relationships']}")
print(f"Processing time: {stats['duration']}")

# Detailed logging
logger.info("Processing batch job", extra={
    'batch_id': batch_id,
    'files_processed': len(files),
    'success_rate': success_rate
})
```

## Examples and Tutorials

See the `examples/` directory for comprehensive examples:

- `basic_usage.py`: Simple processing example
- `advanced_config.py`: Custom configuration example
- `custom_ontology.py`: Domain-specific vocabulary integration
- `batch_monitoring.py`: Production monitoring setup

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for guidelines.

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd automated-kg-generator

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black automated_kg_generator.py
isort automated_kg_generator.py
```

## License

This project is licensed under the MIT License - see `LICENSE` file for details.

## Support

- **Documentation**: Full API documentation available at [docs link]
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our community discussions
- **Commercial Support**: Contact us for enterprise support options

## Roadmap

### Upcoming Features
- [ ] Support for additional file formats (XML, PDF, DOCX)
- [ ] Graph visualization and exploration tools
- [ ] Integration with graph databases (Neo4j, Amazon Neptune)
- [ ] Real-time processing capabilities
- [ ] Multi-language support for text processing
- [ ] Advanced relationship inference using graph algorithms

### Performance Improvements
- [ ] GPU acceleration for large-scale processing
- [ ] Distributed processing with Apache Spark
- [ ] Advanced caching and memoization
- [ ] Streaming RDF generation for memory efficiency

## Acknowledgments

- OpenAI for providing advanced language models and Batch API
- RDFLib team for excellent RDF processing capabilities
- LangChain community for document loading infrastructure
- Contributors and early adopters for feedback and testing

---

**Built with ❤️ for the Semantic Web and Knowledge Graph community**
