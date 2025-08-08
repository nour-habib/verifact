import time

from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import APIRouter, HTTPException, Request

from src.models.factcheck import Claim, FactCheckOptions, FactCheckRequest, FactCheckResponse, Source
from openai import OpenAI

from src.verifact_agents.verdict_writer import VerdictWriter
from src.verifact_agents.claim_detector import ClaimDetector
from src.verifact_agents.evidence_hunter import EvidenceHunter
import asyncio
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

currentModel = os.getenv("OPENAI_MODEL")

router = APIRouter(prefix="/api/v1")

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)
limit_per_minute = "10/minute"


@router.post("/factcheck", response_model=FactCheckResponse)
@limiter.limit(limit_per_minute) 
async def factcheck(request: FactCheckRequest, http_request: Request):
    start_time = time.time()

    """Request object required for slowapi to work"""

    #use request object to get user ip

    user_ip = get_remote_address()
    if(not check_rate_limiting(user_ip)):
        print("Rate limit exceeded")
        #Throw error
    

     


    #1

    #request validation
    #check if null/empty
    #AI advice: FastAPI's built in  validation is robust enough -> verify later

    #2

    # Extract the text to be fact-checked from the request
    text_to_check = request.text
    if(text_to_check is None):
        raise HTTPException(status_code=404, detail="Claim not found")
    
    options = request.options or FactCheckOptions()
    # TODO: Implement actual fact-checking logic here
    # This is a placeholder response

    claim_detector_agent = ClaimDetector()
    evidence_agent = EvidenceHunter() 
    verdict_agent = VerdictWriter(explanation_detail=options.explanation_detail)

    claims = await claim_detector_agent.detect_claims(text_to_check)
    print("sample_claims: " , claims)

    claims_with_options = []

    for claim in claims:
        if((claim.check_worthiness >= options.min_check_worthiness) and (options.domains.__contains__(claim.domain))):
            claims_with_options.append(claim)
            # Stop adding claims once we reach the max_claims limit
            if len(claims_with_options) >= options.max_claims:
                break
     
    print(f"Filtered claims: {len(claims_with_options)} out of {len(claims)} total claims")

    evidence = await evidence_agent.gather_evidence(claims_with_options)
    print("Evidence found:", evidence)

    verdict = await verdict_agent.write_verdict(text_to_check, evidence)
    print("The_verdict: ", verdict)

   
    return FactCheckResponse(
        claims=[
            Claim(
                text=text_to_check,
                verdict=verdict.verdict,
                confidence=verdict.confidence,
                explanation=verdict.explanation,
                sources=verdict.sources
            )
        ],
        metadata={
            "processing_time": f"{time.time() - start_time:.1f}s",
            "model_version": "1.0.4",
            "input_length": len(text_to_check),
            "options_used": {
                "min_check_worthiness": options.min_check_worthiness,
                "domains": options.domains,
                "max_claims": options.max_claims,
                "explanation_detail": options.explanation_detail,
            },
        },
    )

#TODO implement rate limiting, see prompt or notes

def check_rate_limiting():
    #init local cach
    #start start time
    #store ip/user id
    #store timestamp and ip/id  in cache or storage
    #keep track of how many requests werwe made in the last 60 seconds
    
    #currrent - window duration
    #count requests within the window
    #compare against limit
    pass



@router.get("/factcheck/{factcheck_id}", response_model=FactCheckResponse)
async def get_factcheck_by_id(factcheck_id: str):
    """Database models not implemented so hold off on this"""
    #Chck supabase code






async def main():
    request = FactCheckRequest(text="Canada's population has been increasing")
    response = await factcheck(request)
    print("response: ", response)


if __name__ == "__main__":
    asyncio.run(main())
