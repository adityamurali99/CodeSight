import asyncio
import httpx
from reviewer import analyze_code
from schemas import ReviewResponse

DIFF_URL = "https://github.com/adityamurali99/CodeSight/pull/1.diff" 

async def test_end_to_end():
    print(f"📡 Testing Fetch from: {DIFF_URL}")
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "CodeSight-Test-Client"
        }
        
        try:
            response = await client.get(DIFF_URL, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                print(f"❌ Fetch Failed! Status: {response.status_code}")
                print(f"Response: {response.text}")
                return

            diff_text = response.text
            print(f"✅ Fetch Successful! ({len(diff_text)} characters)")
            
            # Show a snippet of what we fetched
            print("\n--- DIFF PREVIEW ---")
            print("\n".join(diff_text.splitlines()[:10]))
            
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return

    # 2. RUN ANALYSIS
    print(f"\n🚀 Running AI Analysis...")
    
    mock_graph = type('Mock', (object,), {
        'get_context': lambda self, c, hops: "mock_context",
        'get_impact_analysis': lambda self, c, hops: "mock_impact"
    })()

    try:
        review = await analyze_code(diff_text, mock_graph)
        print(f"\n--- AI RESPONSE ---")
        print(f"Summary: {review.summary}")
        print(f"Findings: {len(review.findings)} issues found.")
        for i, f in enumerate(review.findings, 1):
            print(f"  {i}. [{f.category.upper()}] Line {f.line_number}: {f.issue}")
            
    except Exception as e:
        print(f"\n--- ANALYSIS CRASH ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())