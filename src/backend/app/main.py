from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import io
import pandas as pd

from .models import MatchRequest, MatchResponse, MatchResult, UploadResponse, HealthResponse, ExportRequest
from .tfidf_model import TFIDFModel
from .data_parser import DataParser

# Global variables
search_model = None
dataset = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global search_model
    print("API starting up...")
    print("Waiting for dataset upload...")
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="TF-IDF Connection Matcher API",
    description="Upload dataset and match people based on professional background",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "TF-IDF Connection Matcher API",
        "endpoints": {
            "POST /upload": "Upload Excel dataset",
            "POST /match": "Find matching connections",
            "GET /health": "Check API status"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check if the API has a dataset loaded."""
    return HealthResponse(
        status="healthy",
        dataset_loaded=dataset is not None,
        dataset_size=len(dataset) if dataset is not None else 0
    )

@app.post("/upload", response_model=UploadResponse, tags=["Data"])
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload an Excel file containing the dataset.
    
    Expected columns:
    - Name
    - Professional Title/Employment & Career
    - Board Service
    """
    global dataset, search_model
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Parse the dataset
        parser = DataParser()
        df = parser.parse_excel_bytes(io.BytesIO(contents))
        
        # Validate required columns exist
        required_cols = ['name', 'employment', 'board_service', 'employment_norm', 'board_service_norm']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset missing required columns after parsing: {missing}"
            )
        
        # Store the dataset globally
        dataset = df
        
        # Initialize and fit the TF-IDF model
        search_model = TFIDFModel(max_features=10000, ngram_range=(1, 2))
        search_model.fit_corpus(df, ['employment_norm', 'board_service_norm'])
        
        return UploadResponse(
            status="success",
            message=f"Dataset uploaded and indexed successfully",
            rows_loaded=len(df),
            columns=df.columns.tolist()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/match", response_model=MatchResponse, tags=["Search"])
async def match_connections(request: MatchRequest):
    """
    Find matching people based on professional background.
    
    - **query**: Description of person to match (employment, board service, etc.)
    - **top_k**: Number of matches to return (default: 10, max: 100)
    - **min_score**: Minimum normalized score threshold 0-1 (default: 0.8)
    """
    if search_model is None or dataset is None:
        raise HTTPException(
            status_code=400, 
            detail="No dataset loaded. Please upload a dataset first using /upload endpoint."
        )
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    print(f"Received match request: query='{request.query[:50]}...', top_k={request.top_k}, min_score={request.min_score}")
    
    # Perform TF-IDF search with normalized scores and filtering
    results_df = search_model.rank(request.query, top_k=request.top_k, min_score=request.min_score)
    
    # Handle case where no results meet threshold
    if results_df.empty:
        return MatchResponse(
            query=request.query,
            total_matches=0,
            matches=[]
        )
    
    # Convert to response format
    matches = []
    for idx, row in results_df.iterrows():
        matches.append(MatchResult(
            name=row['name'],
            employment=row['employment'],
            board_service=row['board_service'],
            score=float(row['tfidf_score']),
            rank=idx + 1
        ))
    
    return MatchResponse(
        query=request.query,
        total_matches=len(matches),
        matches=matches
    )

@app.post("/export", tags=["Export"])
async def export_matches(request: ExportRequest):
    """
    Export match results to Excel file.
    """
    if not request.matches:
        raise HTTPException(status_code=400, detail="No matches to export")
    
    try:
        # Convert matches to DataFrame
        data = []
        for match in request.matches:
            data.append({
                'Name': match.name,
                'Employment': match.employment,
                'Board Service': match.board_service,
                'Match Score': match.score,
                'Rank': match.rank
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Matches')
        
        output.seek(0)
        
        # Return as downloadable file
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=board_matches.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting file: {str(e)}")