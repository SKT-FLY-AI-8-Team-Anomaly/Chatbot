from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os

# 우리가 만든 RAG 모듈 가져오기
from flyaichatbot import RAGApp

# ==========================================
# 1. 데이터 모델 정의 (Pydantic)
# ==========================================
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

# ==========================================
# 2. 전역 RAG 인스턴스 및 수명 주기 설정
# ==========================================
# RAGApp 인스턴스 생성
rag_service = RAGApp(data_path='./datas', db_path='./chroma_db')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작 시 실행: DB 로드 및 체인 빌드
    서버 종료 시 실행: 리소스 정리 (현재는 없음)
    """
    print("🚀 Server starting... Loading RAG system.")
    
    # DB 폴더가 없으면 새로 임베딩, 있으면 로드만 수행
    if not os.path.exists(rag_service.db_path):
        print("Creating new Vector DB...")
        rag_service.load_and_embed()
    else:
        print("Loading existing Vector DB...")
        rag_service.get_retriever()
    
    # 체인 미리 빌드 (첫 요청 속도 향상) - 벡터 DB가 있을 때만
    if rag_service.vectorstore:
        rag_service.build_chain()
        print("✅ RAG system is ready.")
    else:
        print("⚠️  RAG system started without vector DB. Please add documents to 'datas' folder.")
    
    yield
    
    print("🛑 Server shutting down.")

# ==========================================
# 3. FastAPI 앱 초기화
# ==========================================
app = FastAPI(
    title="RAG Chatbot API",
    description="Markdown 문서 기반 질의응답 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. 엔드포인트 정의
# ==========================================
@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """
    사용자의 질문을 받아 RAG 모델의 답변을 반환합니다.
    """
    print(f"📥 요청 받음: {request.question}")
    
    if not request.question.strip():
        print("❌ 빈 질문 요청")
        raise HTTPException(status_code=422, detail="질문 내용이 비어있습니다.")

    try:
        print(f"🤖 RAG 모델 처리 중...")
        # RAGApp의 ask 메서드 호출
        response_text = rag_service.ask(request.question)
        
        # 응답이 None이거나 빈 값인 경우 처리
        if response_text is None:
            response_text = "죄송합니다. 답변을 생성할 수 없습니다."
        elif not isinstance(response_text, str):
            response_text = str(response_text)
        
        print(f"✅ 응답 생성 완료: {response_text[:50]}...")
        return QueryResponse(answer=response_text)
    
    except Exception as e:
        # 에러 발생 시 500 에러 리턴
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """서버 상태 확인용"""
    return {"status": "ok"}

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - 질의응답 엔드포인트",
            "/health": "GET - 서버 상태 확인"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
