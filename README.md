\# AI Project Intelligence \& Risk Advisor



An AI-powered project intelligence platform designed to extract information from project documents and support document retrieval for project analysis and risk management.



\## Overview



The platform processes project documents, divides extracted text into manageable chunks, generates semantic embeddings, and stores them in a FAISS vector index to enable similarity-based retrieval.



\## Features



\- Upload project documents through a Streamlit interface.

\- Extract text from PDF, DOCX, CSV, and TXT files.

\- Split text into configurable chunks with overlap.

\- Generate embeddings using `all-MiniLM-L6-v2`.

\- Store and retrieve relevant text using FAISS.

\- Run the document-processing pipeline from an interactive interface.



\## Technology Stack



\- Python

\- Streamlit

\- Sentence Transformers

\- FAISS

\- PyPDF

\- python-docx

\- Pandas



\## Project Structure



```text

AI\_Project\_Intelligence\_and\_Risk\_Advisor/

├── app.py

├── document\_loader.py

├── text\_chunker.py

├── embedding\_generator.py

├── vector\_store.py

├── document\_pipeline.py

├── create\_test\_documents.py

├── test\_document\_loader.py

├── test\_document\_pipeline.py

├── test\_embedding\_generator.py

├── test\_text\_chunker.py

├── test\_vector\_store.py

├── sample\_report.pdf

├── sample\_report.docx

├── sample\_tasks.csv

├── .gitignore

├── LICENSE

└── README.md

```



\## Getting Started



\### 1. Clone the repository



```bash

git clone <YOUR\_GITHUB\_REPOSITORY\_URL>

cd AI\_Project\_Intelligence\_and\_Risk\_Advisor

```



\### 2. Create a virtual environment



```bash

python -m venv .venv

```



Activate it on Windows:



```cmd

.venv\\Scripts\\activate

```



\### 3. Install dependencies



Install the libraries used by the project:



```bash

pip install streamlit pypdf python-docx pandas sentence-transformers faiss-cpu

```



\### 4. Run the application



```bash

streamlit run app.py

```



\## Testing



Run the tests using Python's unittest framework where applicable, or use the test commands documented in the individual test files.



\## License



This project is licensed under the MIT License. See the \[LICENSE](LICENSE) file for details.



\## Acknowledgements



Developed as part of the Infosys Springboard virtual internship project.



