# RATAN Demo Script & Preparation Guide

This guide provides a structured script and checklist for demonstrating the RATAN platform live to recruiters, engineering teams, or in a portfolio video. 

## Preparation Checklist
Before starting the demo, ensure the following:
- [ ] Both Frontend (`npm run dev`) and Backend (`uvicorn app.main:app --reload`) are running smoothly.
- [ ] Have 2 distinct PDF files ready to upload (e.g., an industrial pump manual and a standard company policy document).
- [ ] Ensure Qdrant is running (or Docker container is active).
- [ ] Clear previous test users from the database if you want to show a clean registration flow.
- [ ] Open the browser network tab to showcase the SSE (Server-Sent Events) stream.

## Demo Flow (The 5-Minute Script)

### 1. Introduction (30 seconds)
**Action:** Show the landing page.
**Script:** 
> "Welcome to RATAN. This is a full-stack Enterprise Knowledge Platform I developed to solve the problem of siloed technical documentation. It utilizes a highly optimized Retrieval-Augmented Generation (RAG) pipeline to allow both individuals and large organizations to instantly query their documents securely. Let me show you how it works."

### 2. Authentication & Multi-Tenancy (45 seconds)
**Action:** Log in as an Enterprise User (e.g., Admin for 'Stark Industries'). Navigate to the Dashboard.
**Script:** 
> "Security and isolation were primary architectural requirements. When I log in, the Next.js frontend securely stores a Stateless JWT. This token contains my role and tenant ID. The backend FastAPI service validates this cryptographically on every request, ensuring that my searches and file uploads are strictly isolated to my organization's namespace. A user from a different organization physically cannot retrieve my documents."

### 3. Document Ingestion (1 minute)
**Action:** Go to the Upload/Documents tab. Drag and drop the technical PDF.
**Script:** 
> "Let's upload a 50-page hydraulic pump manual. When I upload this, the backend doesn't just store it in Backblaze B2. It initiates a processing pipeline. It extracts the text, chunks it into semantically meaningful blocks using LangChain, and generates dense vector embeddings locally using the BGE-Small model. I implemented a lazy-loading Singleton pattern for the embedding model to ensure this entire process runs entirely under a 512MB RAM constraint, preventing the cloud server from crashing."

### 4. Real-time RAG & Streaming Chat (1.5 minutes)
**Action:** Open the Chat interface. Ask a specific, complex question about the uploaded document. **Important: Keep the Network tab open to show the `/message` endpoint.**
**Script:** 
> "Now for the core feature: the AI Chat. I'm going to ask a specific question about the torque specifications from that manual. 
> 
> *[Hit Enter]* 
> 
> Notice how the text starts streaming instantly? A common problem with AI apps is the 'loading spinner of death' while waiting for the LLM. I solved this by implementing Server-Sent Events (SSE). The backend queries the Qdrant vector database in milliseconds, builds a context-rich prompt, and asynchronously streams the LLM tokens directly to the React frontend as they are generated. This drops the perceived latency to under 500ms."

**Action:** Point out the Citations UI.
**Script:** 
> "Furthermore, the AI isn't hallucinating. Notice the citations appended at the bottom. The backend maps the exact chunks retrieved from Qdrant and passes that metadata to the UI, allowing the user to trace the AI's answer back to the exact page of the original manual."

### 5. Personal Workspace & Conclusion (1 minute)
**Action:** Log out. Log in with a Personal account (or Google Auth). Show the clean Personal UI.
**Script:** 
> "Finally, the application isn't just for enterprises. I built a parallel Personal AI Workspace. It uses the exact same powerful RAG backend, but routes the vectors to a private namespace unique to the user ID. It’s a completely personalized intelligence layer.
> 
> In summary, RATAN is a production-hardened platform. It features Clean Architecture, 100% test coverage on the AI pipelines, and is optimized for strict cloud memory constraints. Thank you for your time."

## Screenshots & GIF Recommendations for GitHub
If you are putting this on your GitHub README, create GIFs of the following:
1.  **The Streaming Chat:** A 5-second GIF showing a question being asked and the text fluidly typing out on the screen.
2.  **The Upload Process:** Showing a file being dragged and dropped, with the success toast appearing.
3.  **The Glassmorphism UI:** A static screenshot of the Dashboard, highlighting the premium Tailwind CSS design.
