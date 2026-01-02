import os
import time
import shutil
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 환경 변수 로드
load_dotenv(override=True)

class RAGApp:
    def __init__(self, data_path='./datas', db_path='./chroma_db'):
        self.data_path = data_path
        self.db_path = db_path
        
        # 1. 모델 초기화
        # 주의: gpt-5-nano 등은 현재 시점(2024년 기준) 공개되지 않았거나 사용자 지정 모델일 수 있습니다.
        # 실제 사용 가능한 모델명(gpt-4o, gpt-4-turbo 등)을 확인해주세요.
        try:
            self.llm = ChatOpenAI(
                temperature=0.1,
                model="gpt-4o",  # gpt-5-nano-2025-08-07이 없으면 gpt-4o 사용
            )
        except Exception as e:
            print(f"⚠️  모델 초기화 오류: {e}")
            print("   gpt-4o로 재시도합니다...")
            self.llm = ChatOpenAI(
                temperature=0.1,
                model="gpt-4o",
            )
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        self.vectorstore = None
        self.retriever = None
        self.chain = None

    def _load_file(self, file_path):
        try:
            ext = file_path.split('.')[-1].lower()
            if ext == 'md':
                loader = UnstructuredMarkdownLoader(file_path)
            elif ext == 'pdf':
                loader = PyPDFLoader(file_path)
            
            return loader.load()

        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return []

    def load_and_embed(self):
        """문서를 로드하고 배치 단위로 나누어 벡터 저장소에 저장합니다."""
        print(f"Loading documents from {self.data_path}...")
        
        raw_documents = []
        if not os.path.exists(self.data_path):
            print(f"Error: Directory '{self.data_path}' not found.")
            return

        # 폴더 내 파일 순회
        files = os.listdir(self.data_path)
        for file_name in files:
            full_path = os.path.join(self.data_path, file_name)
            
            # 파일인지 확인
            if os.path.isfile(full_path):
                docs = self._load_file(full_path)
                if docs:
                    raw_documents.extend(docs) 

        print(f"총 로드된 문서 수: {len(raw_documents)}")

        # 문서가 없으면 벡터 DB 생성을 건너뜀
        if not raw_documents:
            print("⚠️  Warning: No documents found. Vector DB will not be created.")
            print("   Please add markdown (.md) or PDF (.pdf) files to the 'datas' folder.")
            return

        # 2. 텍스트 분할 (Splitting)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(raw_documents)
        print(f"전체 청크 수: {len(chunks)}")

        # ==========================================
        # 3. 배치 처리 (Batch Processing) - 수정된 부분
        # ==========================================
        batch_size = 100  # 한 번에 처리할 청크 개수 (조절 가능)
        
        # 3-1. 첫 번째 배치로 DB 생성
        print(f"Creating Vector DB with initial batch (Size: {batch_size})...")
        first_batch = chunks[:batch_size]
        
        self.vectorstore = Chroma.from_documents(
            documents=first_batch,
            embedding=self.embeddings,
            persist_directory=self.db_path,
            collection_name="sw_db",
        )

        # 3-2. 나머지 배치 추가 (add_documents 사용)
        total_batches = (len(chunks) - 1) // batch_size + 1
        
        for i in range(batch_size, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            current_batch_idx = (i // batch_size) + 1
            
            print(f"Adding batch {current_batch_idx}/{total_batches} ({len(batch)} chunks)...")
            
            try:
                self.vectorstore.add_documents(batch)
                # API 호출 속도 조절을 위한 대기 (선택 사항)
                time.sleep(0.5) 
            except Exception as e:
                print(f"Error adding batch {current_batch_idx}: {e}")

        print("✅ Vector database created and saved successfully.")

    def get_retriever(self):
        """Retriever를 설정합니다."""
        if not self.vectorstore:
            # 이미 생성된 DB가 있다면 로드
            if os.path.exists(self.db_path):
                self.vectorstore = Chroma(
                    persist_directory=self.db_path,
                    embedding_function=self.embeddings,
                    collection_name="sw_db"
                )
            else:
                print("⚠️  Warning: Vector DB not found. Please add documents first.")
                return None
            
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        return self.retriever

    def build_chain(self):
        """RAG 체인을 구성합니다."""
        retriever = self.get_retriever()
        
        if not retriever:
            return None

        prompt_template = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. 
        Use three sentences maximum and keep the answer concise.
        
        Question: {question} 
        Context: {context} 
        Answer:
        """
        prompt = PromptTemplate.from_template(prompt_template)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # LCEL(LangChain Expression Language) 구조
        self.chain = (
            {
                "context": retriever | format_docs, 
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser() # 모델 출력을 문자열로 변환
        )
        return self.chain

    def ask(self, query: str):
        """질문을 받아 답변을 반환합니다."""
        # 벡터 DB가 없으면 기본 메시지 반환
        if not self.vectorstore:
            return "죄송합니다. 현재 문서 데이터베이스가 없습니다. 관리자에게 문의해주세요."
        
        if not self.chain:
            chain = self.build_chain()
            if not chain:
                return "죄송합니다. 현재 문서 데이터베이스가 없습니다. 관리자에게 문의해주세요."
        
        try:
            return self.chain.invoke(query)
        except Exception as e:
            error_msg = str(e)
            print(f"❌ RAG 처리 오류: {error_msg}")
            
            # API 키 오류인 경우
            if "api_key" in error_msg.lower() or "401" in error_msg or "authentication" in error_msg.lower():
                return "죄송합니다. OpenAI API 키가 설정되지 않았거나 잘못되었습니다. 관리자에게 문의해주세요."
            
            # 모델 오류인 경우
            if "model" in error_msg.lower() or "not found" in error_msg.lower():
                return "죄송합니다. AI 모델에 접근할 수 없습니다. 관리자에게 문의해주세요."
            
            # 기타 오류
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {error_msg[:100]}"


# ==========================================
# 실행부 (Main Execution)
# ==========================================
if __name__ == "__main__":
    # 1. 앱 초기화
    app = RAGApp(data_path='./datas')

    # 2. 데이터 적재 (최초 1회만 수행하거나, 데이터 변경 시 수행)
    # DB가 이미 존재하고 데이터가 같다면 주석 처리해도 됩니다.
    if not os.path.exists('./chroma_db'): 
        app.load_and_embed()
    else:
        # DB 로드만 수행하기 위해 retriever 초기화
        app.get_retriever() 

    # 3. 질문 입력 받기
    print("-" * 30)
    user_question = input("질문을 입력하세요 (종료하려면 'exit' 입력): ")
    
    while user_question.lower() != 'exit':
        if user_question.strip():
            print("\nThinking...")
            answer = app.ask(user_question)
            print(f"\n[Answer]:\n{answer}")
        
        print("-" * 30)
        user_question = input("\n질문을 입력하세요 (종료하려면 'exit' 입력): ")
