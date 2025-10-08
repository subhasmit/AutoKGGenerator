
"""
Automated LLM-Based Knowledge Graph Generator
=============================================

A generic implementation for converting unknown CSV, JSON, and text files 
to RDF Turtle format using LangChain, RDFLib, and OpenAI's Batch API.

Features:
- Automatic file type detection and schema inference
- Batch processing with OpenAI API for cost efficiency
- Comprehensive error handling and validation
- Support for structured outputs with Pydantic models
- Extensible architecture for custom ontologies
"""

import os
import json
import csv
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Core dependencies
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, FOAF, OWL
from rdflib.namespace import XSD, DCTERMS
from pydantic import BaseModel, Field
from openai import OpenAI

# LangChain imports
from langchain_community.document_loaders import CSVLoader, JSONLoader, TextLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured extraction
class EntityType(str, Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    CONCEPT = "Concept"
    EVENT = "Event"
    PRODUCT = "Product"
    OTHER = "Other"

class ExtractedEntity(BaseModel):
    name: str = Field(description="The name or identifier of the entity")
    type: EntityType = Field(description="The type/category of the entity")
    properties: Dict[str, str] = Field(
        default_factory=dict, 
        description="Additional properties and attributes of the entity"
    )
    confidence: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for the entity extraction"
    )

class ExtractedRelationship(BaseModel):
    subject: str = Field(description="The subject entity in the relationship")
    predicate: str = Field(description="The relationship type or predicate")
    object: str = Field(description="The object entity in the relationship")
    confidence: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for the relationship"
    )
    properties: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional properties of the relationship"
    )

class KnowledgeExtractionResult(BaseModel):
    entities: List[ExtractedEntity] = Field(description="List of extracted entities")
    relationships: List[ExtractedRelationship] = Field(description="List of extracted relationships")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the extraction"
    )

@dataclass
class ProcessingJob:
    """Represents a single processing job for the batch API"""
    custom_id: str
    file_path: str
    content: str
    file_type: str
    chunk_index: int = 0

class FileTypeDetector:
    """Automatically detect file types and extract schema information"""

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """Detect file type based on extension and content"""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.csv':
            return 'csv'
        elif extension in ['.json', '.jsonl']:
            return 'json'
        elif extension in ['.txt', '.md', '.text']:
            return 'text'
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)  # Read first 100 chars
                    if content.strip().startswith('{') or content.strip().startswith('['):
                        return 'json'
                    elif ',' in content and '\n' in content:
                        return 'csv'
                    else:
                        return 'text'
            except:
                return 'text'

    @staticmethod
    def infer_csv_schema(file_path: str) -> Dict[str, Any]:
        """Infer schema from CSV file"""
        try:
            df = pd.read_csv(file_path, nrows=5)  # Sample first 5 rows
            schema = {
                'columns': list(df.columns),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'sample_data': df.head(3).to_dict('records'),
                'row_count': len(pd.read_csv(file_path))
            }
            return schema
        except Exception as e:
            logger.error(f"Error inferring CSV schema: {e}")
            return {}

    @staticmethod
    def infer_json_schema(file_path: str) -> Dict[str, Any]:
        """Infer schema from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def get_structure(obj, max_depth=3, current_depth=0):
                if current_depth >= max_depth:
                    return type(obj).__name__

                if isinstance(obj, dict):
                    return {k: get_structure(v, max_depth, current_depth + 1) 
                           for k, v in list(obj.items())[:10]}  # Limit to 10 keys
                elif isinstance(obj, list) and obj:
                    return [get_structure(obj[0], max_depth, current_depth + 1)]
                else:
                    return type(obj).__name__

            schema = {
                'structure': get_structure(data),
                'type': type(data).__name__,
                'size': len(str(data))
            }
            return schema
        except Exception as e:
            logger.error(f"Error inferring JSON schema: {e}")
            return {}

class OpenAIBatchProcessor:
    """Handle OpenAI Batch API operations"""

    def __init__(self, api_key: str, model: str = "gpt-4o-2024-08-06"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def create_extraction_prompt(self, content: str, file_type: str, schema: Dict = None) -> str:
        """Create a comprehensive extraction prompt"""
        base_prompt = f"""
You are an expert knowledge extraction system. Extract structured information from the following {file_type} data.

INSTRUCTIONS:
1. Identify all entities (people, organizations, locations, concepts, events, products)
2. Extract relationships between entities
3. Include confidence scores (0.0-1.0) for each extraction
4. Map entities to standard ontologies when possible (FOAF, Schema.org, DBpedia)
5. Extract temporal information and metadata when available

"""

        if schema:
            base_prompt += f"\nDATA SCHEMA: {json.dumps(schema, indent=2)}\n"

        base_prompt += f"\nDATA TO PROCESS:\n{content}\n"

        return base_prompt

    def prepare_batch_requests(self, jobs: List[ProcessingJob]) -> List[Dict]:
        """Prepare batch requests for OpenAI API"""
        requests = []

        for job in jobs:
            # Detect and infer schema
            if job.file_type == 'csv':
                schema = FileTypeDetector.infer_csv_schema(job.file_path)
            elif job.file_type == 'json':
                schema = FileTypeDetector.infer_json_schema(job.file_path)
            else:
                schema = None

            prompt = self.create_extraction_prompt(job.content, job.file_type, schema)

            request = {
                "custom_id": job.custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at structured knowledge extraction. Always respond with valid JSON matching the specified schema."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "knowledge_extraction",
                            "strict": True,
                            "schema": KnowledgeExtractionResult.model_json_schema()
                        }
                    },
                    "max_tokens": 4000,
                    "temperature": 0.1
                }
            }
            requests.append(request)

        return requests

    def submit_batch(self, requests: List[Dict]) -> str:
        """Submit batch job to OpenAI"""
        # Create JSONL file
        batch_file_path = "batch_input.jsonl"
        with open(batch_file_path, 'w') as f:
            for request in requests:
                f.write(json.dumps(request) + '\n')

        # Upload file
        with open(batch_file_path, 'rb') as f:
            batch_input_file = self.client.files.create(
                file=f,
                purpose="batch"
            )

        # Create batch
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "Knowledge graph extraction batch"}
        )

        logger.info(f"Batch submitted with ID: {batch.id}")
        return batch.id

    def wait_for_batch_completion(self, batch_id: str, poll_interval: int = 60) -> Dict:
        """Wait for batch completion and return results"""
        while True:
            batch = self.client.batches.retrieve(batch_id)
            logger.info(f"Batch status: {batch.status}")

            if batch.status == "completed":
                return batch
            elif batch.status in ["failed", "expired", "cancelled"]:
                raise Exception(f"Batch failed with status: {batch.status}")
            elif batch.status in ["validating", "in_progress", "finalizing"]:
                time.sleep(poll_interval)
            else:
                logger.warning(f"Unknown batch status: {batch.status}")
                time.sleep(poll_interval)

    def download_batch_results(self, batch: Dict) -> List[Dict]:
        """Download and parse batch results"""
        if not batch.output_file_id:
            raise Exception("No output file available")

        file_response = self.client.files.content(batch.output_file_id)
        content = file_response.text

        results = []
        for line in content.strip().split('\n'):
            if line:
                results.append(json.loads(line))

        return results

class RDFGenerator:
    """Generate RDF from extracted knowledge"""

    def __init__(self, base_namespace: str = "http://example.org/kg/"):
        self.graph = Graph()
        self.base_ns = Namespace(base_namespace)
        self._bind_namespaces()

    def _bind_namespaces(self):
        """Bind standard namespaces"""
        self.graph.bind("kg", self.base_ns)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
        self.graph.bind("dcterms", DCTERMS)

        # Bind schema.org
        SCHEMA = Namespace("http://schema.org/")
        self.graph.bind("schema", SCHEMA)

        # Bind DBpedia
        DBPEDIA = Namespace("http://dbpedia.org/ontology/")
        self.graph.bind("dbpedia", DBPEDIA)

    def _create_uri(self, name: str, entity_type: str = "entity") -> URIRef:
        """Create a clean URI from entity name"""
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
        return self.base_ns[f"{entity_type}_{clean_name}"]

    def _map_entity_type_to_class(self, entity_type: EntityType) -> URIRef:
        """Map entity types to RDF classes"""
        mapping = {
            EntityType.PERSON: FOAF.Person,
            EntityType.ORGANIZATION: FOAF.Organization,
            EntityType.LOCATION: self.base_ns.Location,
            EntityType.CONCEPT: self.base_ns.Concept,
            EntityType.EVENT: self.base_ns.Event,
            EntityType.PRODUCT: self.base_ns.Product,
            EntityType.OTHER: self.base_ns.Entity
        }
        return mapping.get(entity_type, self.base_ns.Entity)

    def add_extraction_to_graph(self, extraction: KnowledgeExtractionResult, source_file: str):
        """Add extraction results to RDF graph"""
        # Create entity URIs mapping
        entity_uris = {}

        # Process entities
        for entity in extraction.entities:
            entity_uri = self._create_uri(entity.name, entity.type.value.lower())
            entity_uris[entity.name] = entity_uri

            # Add basic triples
            self.graph.add((entity_uri, RDF.type, self._map_entity_type_to_class(entity.type)))
            self.graph.add((entity_uri, RDFS.label, Literal(entity.name)))

            # Add confidence score
            if entity.confidence > 0:
                self.graph.add((entity_uri, self.base_ns.confidence, Literal(entity.confidence, datatype=XSD.float)))

            # Add source information
            self.graph.add((entity_uri, DCTERMS.source, Literal(source_file)))

            # Add properties
            for prop_name, prop_value in entity.properties.items():
                prop_uri = self.base_ns[prop_name.replace(' ', '_')]
                self.graph.add((entity_uri, prop_uri, Literal(prop_value)))

        # Process relationships
        for rel in extraction.relationships:
            if rel.subject in entity_uris and rel.object in entity_uris:
                subject_uri = entity_uris[rel.subject]
                object_uri = entity_uris[rel.object]

                # Create predicate URI
                predicate_uri = self.base_ns[rel.predicate.replace(' ', '_')]

                # Add relationship triple
                self.graph.add((subject_uri, predicate_uri, object_uri))

                # Add confidence as reification (if needed)
                if rel.confidence > 0 or rel.properties:
                    # Create blank node for statement
                    stmt = self.graph.value(predicate=RDF.type, object=RDF.Statement, any=False) or self.graph.BNode()
                    self.graph.add((stmt, RDF.type, RDF.Statement))
                    self.graph.add((stmt, RDF.subject, subject_uri))
                    self.graph.add((stmt, RDF.predicate, predicate_uri))
                    self.graph.add((stmt, RDF.object, object_uri))

                    if rel.confidence > 0:
                        self.graph.add((stmt, self.base_ns.confidence, Literal(rel.confidence, datatype=XSD.float)))

                    # Add relationship properties
                    for prop_name, prop_value in rel.properties.items():
                        prop_uri = self.base_ns[prop_name.replace(' ', '_')]
                        self.graph.add((stmt, prop_uri, Literal(prop_value)))

    def export_turtle(self, output_file: str) -> str:
        """Export graph as Turtle format"""
        turtle_data = self.graph.serialize(format='turtle')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(turtle_data)

        logger.info(f"RDF graph exported to {output_file}")
        return turtle_data

    def get_statistics(self) -> Dict[str, int]:
        """Get graph statistics"""
        return {
            'total_triples': len(self.graph),
            'unique_subjects': len(set(self.graph.subjects())),
            'unique_predicates': len(set(self.graph.predicates())),
            'unique_objects': len(set(self.graph.objects())),
            'entities': len([s for s in self.graph.subjects() if (s, RDF.type, None) in self.graph])
        }

class AutomatedKGGenerator:
    """Main orchestrator for automated knowledge graph generation"""

    def __init__(self, openai_api_key: str, base_namespace: str = "http://example.org/kg/"):
        self.batch_processor = OpenAIBatchProcessor(openai_api_key)
        self.rdf_generator = RDFGenerator(base_namespace)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=3000,  # Reasonable size for batch processing
            chunk_overlap=200,
            separator="\n"
        )

    def load_documents(self, directory_path: str) -> List[Document]:
        """Load documents from directory using LangChain loaders"""
        documents = []

        for file_path in Path(directory_path).rglob('*'):
            if file_path.is_file():
                file_type = FileTypeDetector.detect_file_type(str(file_path))

                try:
                    if file_type == 'csv':
                        loader = CSVLoader(str(file_path))
                    elif file_type == 'json':
                        loader = JSONLoader(str(file_path), jq_schema='.')
                    else:  # text
                        loader = TextLoader(str(file_path))

                    docs = loader.load()
                    for doc in docs:
                        doc.metadata['file_path'] = str(file_path)
                        doc.metadata['file_type'] = file_type

                    documents.extend(docs)
                    logger.info(f"Loaded {len(docs)} documents from {file_path}")

                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

        return documents

    def prepare_processing_jobs(self, documents: List[Document]) -> List[ProcessingJob]:
        """Prepare documents for batch processing"""
        jobs = []

        for doc_idx, document in enumerate(documents):
            # Split large documents into chunks
            if len(document.page_content) > 3000:
                chunks = self.text_splitter.split_text(document.page_content)
                for chunk_idx, chunk in enumerate(chunks):
                    job = ProcessingJob(
                        custom_id=f"doc_{doc_idx}_chunk_{chunk_idx}",
                        file_path=document.metadata.get('file_path', 'unknown'),
                        content=chunk,
                        file_type=document.metadata.get('file_type', 'text'),
                        chunk_index=chunk_idx
                    )
                    jobs.append(job)
            else:
                job = ProcessingJob(
                    custom_id=f"doc_{doc_idx}",
                    file_path=document.metadata.get('file_path', 'unknown'),
                    content=document.page_content,
                    file_type=document.metadata.get('file_type', 'text')
                )
                jobs.append(job)

        logger.info(f"Created {len(jobs)} processing jobs")
        return jobs

    def process_batch_results(self, results: List[Dict]) -> List[KnowledgeExtractionResult]:
        """Process batch API results"""
        extractions = []

        for result in results:
            if result.get('response') and result['response'].get('body'):
                try:
                    content = result['response']['body']['choices'][0]['message']['content']
                    extraction_data = json.loads(content)
                    extraction = KnowledgeExtractionResult(**extraction_data)
                    extractions.append(extraction)
                except Exception as e:
                    logger.error(f"Error processing result {result.get('custom_id')}: {e}")

        logger.info(f"Successfully processed {len(extractions)} extractions")
        return extractions

    def generate_knowledge_graph(self, input_directory: str, output_file: str = "knowledge_graph.ttl") -> Dict[str, Any]:
        """Main method to generate knowledge graph from directory"""
        logger.info(f"Starting knowledge graph generation from {input_directory}")

        # Step 1: Load documents
        documents = self.load_documents(input_directory)
        if not documents:
            raise ValueError("No documents found in the specified directory")

        # Step 2: Prepare processing jobs
        jobs = self.prepare_processing_jobs(documents)
        if not jobs:
            raise ValueError("No processing jobs created")

        # Step 3: Submit batch job
        requests = self.batch_processor.prepare_batch_requests(jobs)
        batch_id = self.batch_processor.submit_batch(requests)

        # Step 4: Wait for completion
        logger.info("Waiting for batch processing to complete...")
        completed_batch = self.batch_processor.wait_for_batch_completion(batch_id)

        # Step 5: Download results
        results = self.batch_processor.download_batch_results(completed_batch)

        # Step 6: Process results
        extractions = self.process_batch_results(results)

        # Step 7: Generate RDF
        for extraction in extractions:
            # Find corresponding job to get source file info
            job_id = None
            for result in results:
                if result.get('custom_id'):
                    job_id = result['custom_id']
                    break

            source_file = f"batch_job_{job_id}" if job_id else "unknown"
            self.rdf_generator.add_extraction_to_graph(extraction, source_file)

        # Step 8: Export RDF
        turtle_data = self.rdf_generator.export_turtle(output_file)
        stats = self.rdf_generator.get_statistics()

        # Cleanup
        if os.path.exists("batch_input.jsonl"):
            os.remove("batch_input.jsonl")

        return {
            'output_file': output_file,
            'statistics': stats,
            'batch_id': batch_id,
            'total_documents': len(documents),
            'total_jobs': len(jobs),
            'successful_extractions': len(extractions)
        }

# Usage example and CLI interface
def main():
    """Main function with example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated Knowledge Graph Generator")
    parser.add_argument("--input-dir", required=True, help="Input directory containing CSV, JSON, and text files")
    parser.add_argument("--output-file", default="knowledge_graph.ttl", help="Output RDF Turtle file")
    parser.add_argument("--openai-api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--base-namespace", default="http://example.org/kg/", help="Base RDF namespace")

    args = parser.parse_args()

    # Get API key
    api_key = args.openai_api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key must be provided via --openai-api-key or OPENAI_API_KEY environment variable")

    # Initialize generator
    generator = AutomatedKGGenerator(api_key, args.base_namespace)

    try:
        # Generate knowledge graph
        result = generator.generate_knowledge_graph(args.input_dir, args.output_file)

        print("\n=== Knowledge Graph Generation Complete ===")
        print(f"Output file: {result['output_file']}")
        print(f"Total triples: {result['statistics']['total_triples']}")
        print(f"Unique entities: {result['statistics']['entities']}")
        print(f"Documents processed: {result['total_documents']}")
        print(f"Batch jobs: {result['total_jobs']}")
        print(f"Successful extractions: {result['successful_extractions']}")

    except Exception as e:
        logger.error(f"Error generating knowledge graph: {e}")
        raise

if __name__ == "__main__":
    main()
