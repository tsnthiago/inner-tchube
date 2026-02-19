https://github.com/google-gemini/cookbook/blob/main/examples/Talk_to_documents_with_embeddings.ipynb
https://github.com/google-gemini/cookbook/blob/main/examples/Classify_text_with_embeddings.ipynb
https://github.com/google-gemini/cookbook/blob/main/examples/clustering_with_embeddings.ipynb
https://github.com/google-gemini/cookbook/blob/main/examples/qdrant/Qdrant_similarity_search.ipynb
https://github.com/google-gemini/cookbook/blob/main/examples/qdrant/Movie_Recommendation.ipynb
https://github.com/google-gemini/cookbook/blob/main/examples/qdrant/Hybrid_Search_Legal.ipynb
https://github.com/qdrant/qdrant/blob/master/docs/QUICK_START.md
https://github.com/qdrant/qdrant-client


Skip to main content
Gemini API
Search
/


English
Get API key
Cookbook
Community

Thiago
Docs
API reference

Home
Gemini API
Docs
Embeddings



The Gemini API offers text embedding models to generate embeddings for words, phrases, sentences, and code. Embeddings tasks such as semantic search, classification, and clustering, providing more accurate, context-aware results than keyword-based approaches.

Building Retrieval Augmented Generation (RAG) systems is a common use case for AI products. Embeddings play a key role in significantly enhancing model outputs with improved factual accuracy, coherence, and contextual richness. If you prefer to use a managed RAG solution, we built the File Search tool which makes doing RAG easier to manage and more cost effective.

Generating embeddings
Use the embedContent method to generate text embeddings:

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

result = client.models.embed_content(
        model="gemini-embedding-001",
        contents="What is the meaning of life?"
)

print(result.embeddings)
You can also generate embeddings for multiple chunks at once by passing them in as a list of strings.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

result = client.models.embed_content(
        model="gemini-embedding-001",
        contents= [
            "What is the meaning of life?",
            "What is the purpose of existence?",
            "How do I bake a cake?"
        ]
)

for embedding in result.embeddings:
    print(embedding)
Specify task type to improve performance
You can use embeddings for a wide range of tasks from classification to document search. Specifying the right task type helps optimize the embeddings for the intended relationships, maximizing accuracy and efficiency. For a complete list of supported task types, see the Supported task types table.

The following example shows how you can use SEMANTIC_SIMILARITY to check how similar in meaning strings of texts are.

Note: Cosine similarity is a good distance metric because it focuses on direction rather than magnitude, which more accurately reflects conceptual closeness. Values range from -1 (opposite) to 1 (greatest similarity).
Python
JavaScript
Go
REST

from google import genai
from google.genai import types
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

client = genai.Client()

texts = [
    "What is the meaning of life?",
    "What is the purpose of existence?",
    "How do I bake a cake?",
]

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=texts,
    config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
)

# Create a 3x3 table to show the similarity matrix
df = pd.DataFrame(
    cosine_similarity([e.values for e in result.embeddings]),
    index=texts,
    columns=texts,
)

print(df)
The code snippets will show how similar the different chunks of text are to one another when run.

Supported task types
Task type	Description	Examples
SEMANTIC_SIMILARITY	Embeddings optimized to assess text similarity.	Recommendation systems, duplicate detection
CLASSIFICATION	Embeddings optimized to classify texts according to preset labels.	Sentiment analysis, spam detection
CLUSTERING	Embeddings optimized to cluster texts based on their similarities.	Document organization, market research, anomaly detection
RETRIEVAL_DOCUMENT	Embeddings optimized for document search.	Indexing articles, books, or web pages for search.
RETRIEVAL_QUERY	Embeddings optimized for general search queries. Use RETRIEVAL_QUERY for queries; RETRIEVAL_DOCUMENT for documents to be retrieved.	Custom search
CODE_RETRIEVAL_QUERY	Embeddings optimized for retrieval of code blocks based on natural language queries. Use CODE_RETRIEVAL_QUERY for queries; RETRIEVAL_DOCUMENT for code blocks to be retrieved.	Code suggestions and search
QUESTION_ANSWERING	Embeddings for questions in a question-answering system, optimized for finding documents that answer the question. Use QUESTION_ANSWERING for questions; RETRIEVAL_DOCUMENT for documents to be retrieved.	Chatbox
FACT_VERIFICATION	Embeddings for statements that need to be verified, optimized for retrieving documents that contain evidence supporting or refuting the statement. Use FACT_VERIFICATION for the target text; RETRIEVAL_DOCUMENT for documents to be retrieved	Automated fact-checking systems
Controlling embedding size
The Gemini embedding model, gemini-embedding-001, is trained using the Matryoshka Representation Learning (MRL) technique which teaches a model to learn high-dimensional embeddings that have initial segments (or prefixes) which are also useful, simpler versions of the same data.

Use the output_dimensionality parameter to control the size of the output embedding vector. Selecting a smaller output dimensionality can save storage space and increase computational efficiency for downstream applications, while sacrificing little in terms of quality. By default, it outputs a 3072-dimensional embedding, but you can truncate it to a smaller size without losing quality to save storage space. We recommend using 768, 1536, or 3072 output dimensions.

Python
JavaScript
Go
REST

from google import genai
from google.genai import types

client = genai.Client()

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents="What is the meaning of life?",
    config=types.EmbedContentConfig(output_dimensionality=768)
)

[embedding_obj] = result.embeddings
embedding_length = len(embedding_obj.values)

print(f"Length of embedding: {embedding_length}")
Example output from the code snippet:


Length of embedding: 768
Ensuring quality for smaller dimensions
The 3072 dimension embedding is normalized. Normalized embeddings produce more accurate semantic similarity by comparing vector direction, not magnitude. For other dimensions, including 768 and 1536, you need to normalize the embeddings as follows:

Python

import numpy as np
from numpy.linalg import norm

embedding_values_np = np.array(embedding_obj.values)
normed_embedding = embedding_values_np / np.linalg.norm(embedding_values_np)

print(f"Normed embedding length: {len(normed_embedding)}")
print(f"Norm of normed embedding: {np.linalg.norm(normed_embedding):.6f}") # Should be very close to 1
Example output from this code snippet:


Normed embedding length: 768
Norm of normed embedding: 1.000000
The following table shows the MTEB scores, a commonly used benchmark for embeddings, for different dimensions. Notably, the result shows that performance is not strictly tied to the size of the embedding dimension, with lower dimensions achieving scores comparable to their higher dimension counterparts.

MRL Dimension	MTEB Score
2048	68.16
1536	68.17
768	67.99
512	67.55
256	66.19
128	63.31
Use cases
Text embeddings are crucial for a variety of common AI use cases, such as:

Retrieval-Augmented Generation (RAG): Embeddings enhance the quality of generated text by retrieving and incorporating relevant information into the context of a model.
Information retrieval: Search for the most semantically similar text or documents given a piece of input text.

Document search tutorialtask

Search reranking: Prioritize the most relevant items by semantically scoring initial results against the query.

Search reranking tutorialtask

Anomaly detection: Comparing groups of embeddings can help identify hidden trends or outliers.

Anomaly detection tutorialbubble_chart

Classification: Automatically categorize text based on its content, such as sentiment analysis or spam detection

Classification tutorialtoken

Clustering: Effectively grasp complex relationships by creating clusters and visualizations of your embeddings.

Clustering visualization tutorialbubble_chart

Storing embeddings
As you take embeddings to production, it is common to use vector databases to efficiently store, index, and retrieve high-dimensional embeddings. Google Cloud offers managed data services that can be used for this purpose including BigQuery, AlloyDB, and Cloud SQL.

The following tutorials show how to use other third party vector databases with Gemini Embedding.

ChromaDB tutorialsbolt
QDrant tutorialsbolt
Weaviate tutorialsbolt
Pinecone tutorialsbolt
Model versions
Property	Description
Model code
Gemini API

gemini-embedding-001

Supported data types
Input

Text

Output

Text embeddings

Token limits[*]
Input token limit

2,048

Output dimension size

Flexible, supports: 128 - 3072, Recommended: 768, 1536, 3072

Versions	
Read the model version patterns for more details.
Stable: gemini-embedding-001
Latest update	June 2025
For deprecated Embeddings models, visit the Deprecations page

Batch embeddings
If latency is not a concern, try using the Gemini Embeddings model with Batch API. This allows for much higher throughput at 50% of the default Embedding price. Find examples on how to get started in the Batch API cookbook.

Responsible use notice
Unlike generative AI models that create new content, the Gemini Embedding model is only intended to transform the format of your input data into a numerical representation. While Google is responsible for providing an embedding model that transforms the format of your input data to the numerical-format requested, users retain full responsibility for the data they input and the resulting embeddings. By using the Gemini Embedding model you confirm that you have the necessary rights to any content that you upload. Do not generate content that infringes on others' intellectual property or privacy rights. Your use of this service is subject to our Prohibited Use Policy and Google's Terms of Service.

Start building with embeddings
Check out the embeddings quickstart notebook to explore the model capabilities and learn how to customize and visualize your embeddings.

Was this helpful?

Send feedback
Except as otherwise noted, the content of this page is licensed under the Creative Commons Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License. For details, see the Google Developers Site Policies. Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-01-19 UTC.

Terms
Privacy

English
