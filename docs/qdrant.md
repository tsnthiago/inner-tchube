Skip to content
qdrant
qdrant
Repository navigation
Code
Issues
385
 (385)
Pull requests
79
 (79)
Discussions
Actions
Projects
Security
1
 (1)
Insights
Owner avatar
qdrant
Public
qdrant/qdrant
Go to file
t
Name		
agourlaytimvisee
agourlay
and
timvisee
Optimize HNSW plain-search filtered allocation (#8175)
38b5a9a
 · 
44 minutes ago
.config
Decrease retry count on flaky test (#6480)
9 months ago
.github
Push master images to DockerHub (#7836)
last week
config
audit logging (#8071)
last week
docs
missing timeout for payload index ops (#8176)
44 minutes ago
lib
Optimize HNSW plain-search filtered allocation (#8175)
44 minutes ago
openapi
missing timeout for payload index ops (#8176)
44 minutes ago
pkg/appimage
build: AppImage release (#3343)
2 years ago
src
Fix lossy error propagation in consensus (#8156)
18 hours ago
tests
Untagged Enum for FeedbackStrategy (#8171)
18 hours ago
tools
build(deps): bump lodash in /tools/schema2openapi (#7968)
last week
.dockerignore
disk cache hygiene (#6323)
10 months ago
.gitattributes
fix(core): optimize OCI Layers (#7005)
6 months ago
.gitignore
Add a test for recovery after kill during Partial (#7762)
last week
.rusty-hook.toml
Add import formatting rules (#820)
4 years ago
Cargo.lock
WAL: advise mmap to cleanup closed segments (#8164)
18 hours ago
Cargo.toml
WAL: advise mmap to cleanup closed segments (#8164)
18 hours ago
Dockerfile
build(deps): bump lukemathwalker/cargo-chef (#8144)
2 days ago
LICENSE
Create LICENSE
5 years ago
README.md
Add security caution banner to quick start command (#7815)
2 months ago
clippy.toml
Streaming snapshot unpacking (#8025)
last week
rustfmt.toml
Add import formatting rules (#820)
4 years ago
shell.nix
Migrate Python to uv (#7790)
2 months ago
Repository files navigation
README
Code of conduct
Contributing
Apache-2.0 license
Qdrant

Vector Search Engine for the next generation of AI applications

Tests status OpenAPI Docs Apache 2.0 License Discord Roadmap 2025 Qdrant Cloud

Qdrant (read: quadrant) is a vector similarity search engine and vector database. It provides a production-ready service with a convenient API to store, search, and manage points—vectors with an additional payload Qdrant is tailored to extended filtering support. It makes it useful for all sorts of neural-network or semantic-based matching, faceted search, and other applications.

Qdrant is written in Rust 🦀, which makes it fast and reliable even under high load. See benchmarks.

With Qdrant, embeddings or neural network encoders can be turned into full-fledged applications for matching, searching, recommending, and much more!

Qdrant is also available as a fully managed Qdrant Cloud ⛅ including a free tier.

Quick Start • Client Libraries • Demo Projects • Integrations • Contact

Getting Started
Python
pip install qdrant-client
The python client offers a convenient way to start with Qdrant locally:

from qdrant_client import QdrantClient
qdrant = QdrantClient(":memory:") # Create in-memory Qdrant instance, for testing, CI/CD
# OR
client = QdrantClient(path="path/to/db")  # Persists changes to disk, fast prototyping
Client-Server
To experience the full power of Qdrant locally, run the container with this command:

docker run -p 6333:6333 qdrant/qdrant
Caution

Starts an insecure deployment without authentication open to all network interfaces. Please refer to secure your instance.

Now you can connect to this with any client, including Python:

qdrant = QdrantClient("http://localhost:6333") # Connect to existing Qdrant instance
Before deploying Qdrant to production, be sure to read our installation and security guides.

Clients
Qdrant offers the following client libraries to help you integrate it into your application stack with ease:

Official:
Go client
Rust client
JavaScript/TypeScript client
Python client
.NET/C# client
Java client
Community:
Elixir
PHP
Ruby
Java
Where do I go from here?
Quick Start Guide
End to End Colab Notebook demo with SentenceBERT and Qdrant
Detailed Documentation are great starting points
Step-by-Step Tutorial to create your first neural network project with Qdrant
Demo ProjectsRun on Repl.it
Discover Semantic Text Search 🔍
Unlock the power of semantic embeddings with Qdrant, transcending keyword-based search to find meaningful connections in short texts. Deploy a neural search in minutes using a pre-trained neural network, and experience the future of text search. Try it online!

Explore Similar Image Search - Food Discovery 🍕
There's more to discovery than text search, especially when it comes to food. People often choose meals based on appearance rather than descriptions and ingredients. Let Qdrant help your users find their next delicious meal using visual search, even if they don't know the dish's name. Check it out!

Master Extreme Classification - E-commerce Product Categorization 📺
Enter the cutting-edge realm of extreme classification, an emerging machine learning field tackling multi-class and multi-label problems with millions of labels. Harness the potential of similarity learning models, and see how a pre-trained transformer model and Qdrant can revolutionize e-commerce product categorization. Play with it online!

More solutions
API
REST
Online OpenAPI 3.0 documentation is available here. OpenAPI makes it easy to generate a client for virtually any framework or programming language.

You can also download raw OpenAPI definitions.

gRPC
For faster production-tier searches, Qdrant also provides a gRPC interface. You can find gRPC documentation here.

Features
Filtering and Payload
Qdrant can attach any JSON payloads to vectors, allowing for both the storage and filtering of data based on the values in these payloads. Payload supports a wide range of data types and query conditions, including keyword matching, full-text filtering, numerical ranges, geo-locations, and more.

Filtering conditions can be combined in various ways, including should, must, and must_not clauses, ensuring that you can implement any desired business logic on top of similarity matching.

Hybrid Search with Sparse Vectors
To address the limitations of vector embeddings when searching for specific keywords, Qdrant introduces support for sparse vectors in addition to the regular dense ones.

Sparse vectors can be viewed as an generalization of BM25 or TF-IDF ranking. They enable you to harness the capabilities of transformer-based neural networks to weigh individual tokens effectively.

Vector Quantization and On-Disk Storage
Qdrant provides multiple options to make vector search cheaper and more resource-efficient. Built-in vector quantization reduces RAM usage by up to 97% and dynamically manages the trade-off between search speed and precision.

Distributed Deployment
Qdrant offers comprehensive horizontal scaling support through two key mechanisms:

Size expansion via sharding and throughput enhancement via replication
Zero-downtime rolling updates and seamless dynamic scaling of the collections
Highlighted Features
Query Planning and Payload Indexes - leverages stored payload information to optimize query execution strategy.
SIMD Hardware Acceleration - utilizes modern CPU x86-x64 and Neon architectures to deliver better performance.
Async I/O - uses io_uring to maximize disk throughput utilization even on a network-attached storage.
Write-Ahead Logging - ensures data persistence with update confirmation, even during power outages.
Integrations
Examples and/or documentation of Qdrant integrations:

Cohere (blogpost on building a QA app with Cohere and Qdrant) - Use Cohere embeddings with Qdrant
DocArray - Use Qdrant as a document store in DocArray
Haystack - Use Qdrant as a document store with Haystack (blogpost).
LangChain (blogpost) - Use Qdrant as a memory backend for LangChain.
LlamaIndex - Use Qdrant as a Vector Store with LlamaIndex.
OpenAI - ChatGPT retrieval plugin - Use Qdrant as a memory backend for ChatGPT
Microsoft Semantic Kernel - Use Qdrant as persistent memory with Semantic Kernel
Contacts
Have questions? Join our Discord channel or mention @qdrant_engine on Twitter
Want to stay in touch with latest releases? Subscribe to our Newsletters
Looking for a managed cloud? Check pricing, need something personalised? We're at info@qdrant.tech
License
Qdrant is licensed under the Apache License, Version 2.0. View a copy of the License file.

About
Qdrant - High-performance, massive-scale Vector Database and Vector Search Engine for the next generation of AI. Also available in the cloud https://cloud.qdrant.io/

qdrant.tech
Topics
search search-engine machine-learning neural-network nearest-neighbor-search image-search recommender-system search-engines similarity-search ai-search knn-algorithm mlops hnsw vector-search vector-database neural-search vector-search-engine embeddings-similarity ai-search-engine
Resources
 Readme
License
 Apache-2.0 license
Code of conduct
 Code of conduct
Contributing
 Contributing
 Activity
 Custom properties
Stars
 28.9k stars
Watchers
 148 watching
Forks
 2k forks
Report repository
Releases 109
v1.16.3
Latest
on Dec 19, 2025
+ 108 releases
Packages
2
qdrant/qdrant
qdrant
Used by 117
@JustinBacher
@liyang8246
@medelalan
@andrew-d
@Iamshankhadeep
@spectral-team
@stehessel
+ 109
Contributors
156
@dependabot[bot]
@generall
@timvisee
@agourlay
@coszio
@IvanPleshkov
@ffuugoo
@xzfc
@JojiiOfficial
@e-ivkov
@KShivendu
@tellet-q
@allcontributors[bot]
@n0x29a
+ 142 contributors
Deployments
500+
 github-pages 44 minutes ago
+ more deployments
Languages
Rust
87.3%
 
Python
11.4%
 
Shell
0.7%
 
C
0.4%
 
Nix
0.1%
 
Dockerfile
0.1%
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information

# Quick Start

This example covers the most basic use-case - collection creation and basic vector search.
For additional information please refer to the [API documentation](https://api.qdrant.tech/).

## Docker 🐳

Use latest pre-built image from [DockerHub](https://hub.docker.com/r/qdrant/qdrant)

```bash
docker pull qdrant/qdrant
```

Run it with default configuration:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

> [!CAUTION]
> Starts an insecure deployment without authentication open to all network interfaces. Please refer to [secure your instance](https://qdrant.tech/documentation/guides/security/#secure-your-instance).

Build your own from source

```bash
docker build . --tag=qdrant/qdrant
```

And once you need a fine-grained setup, you can also define a storage path and custom configuration:

```bash
docker run -p 6333:6333 \
    -v $(pwd)/path/to/data:/qdrant/storage \
    -v $(pwd)/path/to/snapshots:/qdrant/snapshots \
    -v $(pwd)/path/to/custom_config.yaml:/qdrant/config/production.yaml \
    qdrant/qdrant
```

- `/qdrant/storage` - is the place where Qdrant persists all your data.
  Make sure to mount it as a volume, otherwise docker will drop it with the container.
- `/qdrant/snapshots` - is the place where Qdrant stores [snapshots](https://qdrant.tech/documentation/concepts/snapshots/)
- `/qdrant/config/production.yaml` - is the file with engine configuration. You can override any value from the [reference config](https://github.com/qdrant/qdrant/blob/master/config/config.yaml). In a real production environment, you should enable authentication by setting `service.apiKey`.
- For production environments, consider also setting [`--read-only`](https://docs.docker.com/reference/cli/docker/container/run/#read-only) and `--user=1000:2000` to further secure your Qdrant instance. Or use [our Helm chart](https://github.com/qdrant/qdrant-helm) or [Qdrant Cloud](https://qdrant.tech/documentation/cloud/) which sets these by default.

Now Qdrant should be accessible at [localhost:6333](http://localhost:6333/).

## Create collection

First - let's create a collection with dot-production metric.

```bash
curl -X PUT 'http://localhost:6333/collections/test_collection' \
    -H 'Content-Type: application/json' \
    --data-raw '{
        "vectors": {
          "size": 4,
          "distance": "Dot"
        }
    }'
```

Expected response:

```json
{
  "result": true,
  "status": "ok",
  "time": 0.031095451
}
```

We can ensure that collection was created:

```bash
curl 'http://localhost:6333/collections/test_collection'
```

Expected response:

```json
{
  "result": {
    "status": "green",
    "vectors_count": 0,
    "segments_count": 5,
    "disk_data_size": 0,
    "ram_data_size": 0,
    "config": {
      "params": {
        "vectors": {
          "size": 4,
          "distance": "Dot"
        }
      },
      "hnsw_config": {
        "m": 16,
        "ef_construct": 100,
        "full_scan_threshold": 10000
      },
      "optimizer_config": {
        "deleted_threshold": 0.2,
        "vacuum_min_vector_number": 1000,
        "default_segment_number": 2,
        "max_segment_size": null,
        "memmap_threshold": null,
        "indexing_threshold": 20000,
        "flush_interval_sec": 5,
        "max_optimization_threads": null
      },
      "wal_config": {
        "wal_capacity_mb": 32,
        "wal_segments_ahead": 0
      }
    }
  },
  "status": "ok",
  "time": 2.1199e-5
}
```

## Add points

Let's now add vectors with some payload:

```bash
curl -L -X PUT 'http://localhost:6333/collections/test_collection/points?wait=true' \
    -H 'Content-Type: application/json' \
    --data-raw '{
        "points": [
          {"id": 1, "vector": [0.05, 0.61, 0.76, 0.74], "payload": {"city": "Berlin"}},
          {"id": 2, "vector": [0.19, 0.81, 0.75, 0.11], "payload": {"city": ["Berlin", "London"] }},
          {"id": 3, "vector": [0.36, 0.55, 0.47, 0.94], "payload": {"city": ["Berlin", "Moscow"] }},
          {"id": 4, "vector": [0.18, 0.01, 0.85, 0.80], "payload": {"city": ["London", "Moscow"] }},
          {"id": 5, "vector": [0.24, 0.18, 0.22, 0.44], "payload": {"count": [0] }},
          {"id": 6, "vector": [0.35, 0.08, 0.11, 0.44]}
        ]
    }'
```

Expected response:

```json
{
  "result": {
    "operation_id": 0,
    "status": "completed"
  },
  "status": "ok",
  "time": 0.000206061
}
```

## Search with filtering

Let's start with a basic request:

```bash
curl -L -X POST 'http://localhost:6333/collections/test_collection/points/search' \
    -H 'Content-Type: application/json' \
    --data-raw '{
        "vector": [0.2,0.1,0.9,0.7],
        "top": 3
    }'
```

Expected response:

```json
{
  "result": [
    { "id": 4, "score": 1.362, "payload": null, "version": 0 },
    { "id": 1, "score": 1.273, "payload": null, "version": 0 },
    { "id": 3, "score": 1.208, "payload": null, "version": 0 }
  ],
  "status": "ok",
  "time": 0.000055785
}
```

But result is different if we add a filter:

```bash
curl -L -X POST 'http://localhost:6333/collections/test_collection/points/search' \
    -H 'Content-Type: application/json' \
    --data-raw '{
      "filter": {
          "should": [
              {
                  "key": "city",
                  "match": {
                      "value": "London"
                  }
              }
          ]
      },
      "vector": [0.2, 0.1, 0.9, 0.7],
      "top": 3
  }'
```

Expected response:

```json
{
  "result": [
    { "id": 4, "score": 1.362 },
    { "id": 2, "score": 0.871 }
  ],
  "status": "ok",
  "time": 0.000093972
}
```

Skip to content
qdrant
qdrant-client
Repository navigation
Code
Issues
110
 (110)
Pull requests
27
 (27)
Discussions
Actions
Projects
Security
Insights
Owner avatar
qdrant-client
Public
qdrant/qdrant-client
Go to file
t
Name		
joein
joein
bump version to 1.16.2
49fa101
 · 
2 months ago
.github
Drop python3.9 (#1110)
2 months ago
docs
docs: Reference api.qdrant.tech in README.md instead (#854)
last year
qdrant_client
Fix/lazy load local mode (#1134)
2 months ago
tests
bump version to 1.16.2
2 months ago
tools
Drop python3.9 (#1110)
2 months ago
.gitignore
Connection pooling (#1071)
3 months ago
.pre-commit-config.yaml
Drop black (#623)
2 years ago
LICENSE
Add LICENSE (#75)
4 years ago
README.md
new: rearrange sections in readme, add cloud inference section (#1032)
7 months ago
mypy.ini
update api to v1.0.0 (#101)
3 years ago
netlify.toml
Fastembed 0.5.0 (#870)
2 years ago
poetry.lock
Drop python3.9 (#1110)
2 months ago
pyproject.toml
bump version to 1.16.2
2 months ago
Repository files navigation
README
Apache-2.0 license
Qdrant

Python Client library for the Qdrant vector search engine.

PyPI version OpenAPI Docs Apache 2.0 License Discord Roadmap 2025

Python Qdrant Client
Client library and SDK for the Qdrant vector search engine.

Library contains type definitions for all Qdrant API and allows to make both Sync and Async requests.

Client allows calls for all Qdrant API methods directly. It also provides some additional helper methods for frequently required operations, e.g. initial collection uploading.

See QuickStart for more details!

Installation
pip install qdrant-client
Features
Type hints for all API methods
Local mode - use same API without running server
REST and gRPC support
Minimal dependencies
Extensive Test Coverage
Local mode
Qdrant

Python client allows you to run same code in local mode without running Qdrant server.

Simply initialize client like this:

from qdrant_client import QdrantClient

client = QdrantClient(":memory:")
# or
client = QdrantClient(path="path/to/db")  # Persists changes to disk
Local mode is useful for development, prototyping and testing.

You can use it to run tests in your CI/CD pipeline.
Run it in Colab or Jupyter Notebook, no extra dependencies required. See an example
When you need to scale, simply switch to server mode.
Connect to Qdrant server
To connect to Qdrant server, simply specify host and port:

from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
# or
client = QdrantClient(url="http://localhost:6333")
You can run Qdrant server locally with docker:

docker run -p 6333:6333 qdrant/qdrant:latest
See more launch options in Qdrant repository.

Connect to Qdrant cloud
You can register and use Qdrant Cloud to get a free tier account with 1GB RAM.

Once you have your cluster and API key, you can connect to it like this:

from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://xxxxxx-xxxxx-xxxxx-xxxx-xxxxxxxxx.us-east.aws.cloud.qdrant.io:6333",
    api_key="<your-api-key>",
)
Inference API
Qdrant Client has Inference API that allows to seamlessly create embeddings and use them in Qdrant. Inference API can be used locally with FastEmbed or remotely with models available in Qdrant Cloud.

Local Inference with FastEmbed
pip install qdrant-client[fastembed]
FastEmbed is a library for creating fast vector embeddings on CPU. It is based on ONNX Runtime and allows to run inference both on CPU and GPU.

Qdrant Client can use FastEmbed to create embeddings and upload them to Qdrant. This allows to simplify API and make it more intuitive.

from qdrant_client import QdrantClient, models

# running qdrant in local mode suitable for experiments
client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db") for local mode and persistent storage

model_name = "sentence-transformers/all-MiniLM-L6-v2"
payload = [
    {"document": "Qdrant has Langchain integrations", "source": "Langchain-docs", },
    {"document": "Qdrant also has Llama Index integrations", "source": "LlamaIndex-docs"},
]
docs = [models.Document(text=data["document"], model=model_name) for data in payload]
ids = [42, 2]

client.create_collection(
    "demo_collection",
    vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name), distance=models.Distance.COSINE)
)

client.upload_collection(
    collection_name="demo_collection",
    vectors=docs,
    ids=ids,
    payload=payload,
)

search_result = client.query_points(
    collection_name="demo_collection",
    query=models.Document(text="This is a query document", model=model_name)
).points
print(search_result)
FastEmbed can also utilise GPU for faster embeddings. To enable GPU support, install

pip install 'qdrant-client[fastembed-gpu]'
In order to set GPU, extend documents from the previous example with options.

models.Document(text="To be computed on GPU", model=model_name, options={"cuda": True})
Note: fastembed-gpu and fastembed are mutually exclusive. You can only install one of them.

If you previously installed fastembed, you might need to start from a fresh environment to install fastembed-gpu.

Remote inference with Qdrant Cloud
Qdrant Cloud provides a set of predefined models that can be used for inference without a need to install any additional libraries or host models locally. (Currently available only on paid plans.)

Inference API is the same as in the local mode, but the client has to be instantiated with cloud_inference=True:

from qdrant_client import QdrantClient
client = QdrantClient(
    url="https://xxxxxx-xxxxx-xxxxx-xxxx-xxxxxxxxx.us-east.aws.cloud.qdrant.io:6333",
    api_key="<your-api-key>",
    cloud_inference=True,  # Enable remote inference
)
Note: remote inference requires images to be provided as base64 encoded strings or urls

Examples
Create a new collection

from qdrant_client.models import Distance, VectorParams

client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(size=100, distance=Distance.COSINE),
)
Insert vectors into a collection

import numpy as np

from qdrant_client.models import PointStruct

vectors = np.random.rand(100, 100)
# NOTE: consider splitting the data into chunks to avoid hitting the server's payload size limit
# or use `upload_collection` or `upload_points` methods which handle this for you
# WARNING: uploading points one-by-one is not recommended due to requests overhead
client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(
            id=idx,
            vector=vector.tolist(),
            payload={"color": "red", "rand_number": idx % 10}
        )
        for idx, vector in enumerate(vectors)
    ]
)
Search for similar vectors

query_vector = np.random.rand(100)
hits = client.query_points(
    collection_name="my_collection",
    query=query_vector,
    limit=5  # Return 5 closest points
)
Search for similar vectors with filtering condition

from qdrant_client.models import Filter, FieldCondition, Range

hits = client.query_points(
    collection_name="my_collection",
    query=query_vector,
    query_filter=Filter(
        must=[  # These conditions are required for search results
            FieldCondition(
                key='rand_number',  # Condition based on values of `rand_number` field.
                range=Range(
                    gte=3  # Select only those results where `rand_number` >= 3
                )
            )
        ]
    ),
    limit=5  # Return 5 closest points
)
See more examples in our Documentation!

gRPC
To enable (typically, much faster) collection uploading with gRPC, use the following initialization:

from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", grpc_port=6334, prefer_grpc=True)
Async client
Starting from version 1.6.1, all python client methods are available in async version.

To use it, just import AsyncQdrantClient instead of QdrantClient:

import asyncio

import numpy as np

from qdrant_client import AsyncQdrantClient, models


async def main():
    # Your async code using QdrantClient might be put here
    client = AsyncQdrantClient(url="http://localhost:6333")

    await client.create_collection(
        collection_name="my_collection",
        vectors_config=models.VectorParams(size=10, distance=models.Distance.COSINE),
    )

    await client.upsert(
        collection_name="my_collection",
        points=[
            models.PointStruct(
                id=i,
                vector=np.random.rand(10).tolist(),
            )
            for i in range(100)
        ],
    )

    res = await client.query_points(
        collection_name="my_collection",
        query=np.random.rand(10).tolist(),  # type: ignore
        limit=10,
    )

    print(res)

asyncio.run(main())
Both, gRPC and REST API are supported in async mode. More examples can be found here.

Development
This project uses git hooks to run code formatters.

Set up hooks with pre-commit install before making contributions.

About
Python client for Qdrant vector search engine

qdrant.tech
Topics
vector-search vector-database vector-search-engine qdrant
Resources
 Readme
License
 Apache-2.0 license
 Activity
 Custom properties
Stars
 1.2k stars
Watchers
 8 watching
Forks
 195 forks
Report repository
Releases 52
v1.16.2
Latest
on Dec 12, 2025
+ 51 releases
Packages
No packages published
Contributors
46
@joein
@generall
@coszio
@hh-space-invader
@agourlay
@kacperlukawski
@tellet-q
@NirantK
@timvisee
@monatis
@I8dNLo
@pavelm10
@skvark
@yasyf
+ 32 contributors
Languages
Python
99.6%
 
Shell
0.4%
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
