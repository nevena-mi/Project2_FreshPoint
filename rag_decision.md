RAG Decision Justification
Why We Chose Retrieval-Augmented Generation (RAG)
Project Context

Our application generates LinkedIn posts that combine a user's personal brand with trusted knowledge sources, including books (PDFs), scientific articles, YouTube transcripts, and podcast transcripts. The goal is to create authentic thought-leadership content that reflects both the user's voice and reliable source material, rather than generic AI-generated text.

Initial Approach: Prompt-Based Context Injection

Our initial MVP used a non-RAG approach. During ingestion, each source was split into chunks and assigned topic labels. At generation time, chunks matching the selected topic were injected into the prompt together with the user's personal brand information.

This approach worked well for smaller sources such as articles and YouTube transcripts, where the amount of context remained manageable.

Problems Encountered

Introducing books revealed the limitations of this approach. A single book generates hundreds of chunks, and multiple books quickly exceed the model's practical context window. In addition, users can continuously add new books, articles, podcasts, and videos, meaning the knowledge base is expected to grow over time.

Because retrieval relied on manually assigned topic labels rather than semantic similarity, the system often selected passages that were only loosely related to the intended LinkedIn post. As the source library grew, we observed:

decreasing relevance of retrieved content,
increasingly generic context,
larger prompts,
reduced quality of generated posts.

The addition of books demonstrated that the prompt-injection approach was not scalable.

Why RAG Was the Appropriate Solution

To overcome these limitations, we implemented Retrieval-Augmented Generation (RAG) using semantic embeddings.

Instead of sending large amounts of source material to the language model, our pipeline now:

Splits documents into chunks.
Generates and stores an embedding for each chunk during ingestion.
Embeds the user's requested post angle.
Retrieves only the most semantically relevant chunks.
Uses those retrieved passages as context for generation.

This ensures that the language model receives only the information most relevant to the requested LinkedIn post, improving both scalability and output quality.

Final Decision

We implemented a lightweight RAG pipeline based on semantic embeddings. Each document chunk is embedded once during ingestion and stored for future use. At generation time, only the chunks most semantically similar to the user's requested post angle are retrieved and included in the prompt.

Compared with direct context injection, this approach provides:

scalable handling of a growing document collection,
efficient use of the model's context window,
more relevant retrieval,
stronger grounding in trusted sources,
improved generation quality as the knowledge base expands.

Although RAG introduces additional preprocessing during ingestion, this cost is incurred only once per document. The retrieval step itself remains lightweight and does not require a complex vector database, making it well suited to the scope of our MVP.

For these reasons, we concluded that Retrieval-Augmented Generation was the most appropriate architecture for our application and provides a strong foundation for future expansion.