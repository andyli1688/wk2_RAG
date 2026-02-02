"""
Test script to verify the separated upload and extraction flow
"""
import json
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_FILE = Path(__file__).parent.parent / "storage" / "reports" / "xyz_short_report.txt"

def test_upload_without_extraction():
    """Test that upload returns report_id without claims"""
    print("\n=== Test 1: Upload Without Extraction ===")

    if not TEST_FILE.exists():
        print(f"❌ Test file not found: {TEST_FILE}")
        return None

    with open(TEST_FILE, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{API_BASE_URL}/upload_report", files=files)

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    print(f"✓ Upload successful")
    print(f"  Report ID: {data.get('report_id')}")
    print(f"  Filename: {data.get('filename')}")
    print(f"  File Type: {data.get('file_type')}")
    print(f"  Message: {data.get('message')}")

    # Verify response schema (no claims)
    if 'claims' in data:
        print(f"❌ ERROR: Response should NOT contain 'claims' field")
        return None

    if not all(k in data for k in ['report_id', 'filename', 'file_type', 'message']):
        print(f"❌ ERROR: Response missing required fields")
        return None

    print(f"✓ Response schema is correct (no claims field)")

    return data.get('report_id')


def test_extracted_json_exists(report_id):
    """Verify .extracted.json file was created"""
    print("\n=== Test 2: Verify .extracted.json File ===")

    reports_dir = Path(__file__).parent.parent / "storage" / "reports"
    extracted_file = reports_dir / f"{report_id}.extracted.json"

    if not extracted_file.exists():
        print(f"❌ .extracted.json not found: {extracted_file}")
        return False

    try:
        with open(extracted_file, 'r') as f:
            data = json.load(f)

        print(f"✓ .extracted.json exists and is valid JSON")
        print(f"  Report ID: {data.get('report_id')}")
        print(f"  Filename: {data.get('filename')}")
        print(f"  File Type: {data.get('file_type')}")
        print(f"  Pages: {len(data.get('pages', []))} page(s)")
        print(f"  Extracted At: {data.get('extracted_at')}")

        if not all(k in data for k in ['report_id', 'filename', 'file_type', 'pages', 'extracted_at']):
            print(f"❌ Missing required fields in .extracted.json")
            return False

        return True
    except Exception as e:
        print(f"❌ Error reading .extracted.json: {e}")
        return False


def test_extract_claims(report_id):
    """Test manual claim extraction"""
    print("\n=== Test 3: Manual Claim Extraction ===")

    payload = {'report_id': report_id}

    print(f"Sending extraction request for report: {report_id}")
    print(f"This may take 10-30 seconds for LLM processing...")

    response = requests.post(
        f"{API_BASE_URL}/extract_claims",
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        print(f"❌ Extraction failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    print(f"✓ Extraction successful")
    print(f"  Message: {data.get('message')}")
    print(f"  Claims extracted: {len(data.get('claims', []))}")

    if data.get('claims'):
        first_claim = data['claims'][0]
        print(f"  First claim: {first_claim.get('claim_id')}: {first_claim.get('claim_text')[:50]}...")

    return data.get('claims')


def test_claims_json_exists(report_id):
    """Verify .claims.json file was created"""
    print("\n=== Test 4: Verify .claims.json File ===")

    reports_dir = Path(__file__).parent.parent / "storage" / "reports"
    claims_file = reports_dir / f"{report_id}.claims.json"

    if not claims_file.exists():
        print(f"❌ .claims.json not found: {claims_file}")
        return False

    try:
        with open(claims_file, 'r') as f:
            data = json.load(f)

        claims = data.get('claims', [])
        print(f"✓ .claims.json exists and is valid JSON")
        print(f"  Total claims: {len(claims)}")
        print(f"  Extracted At: {data.get('extracted_at')}")

        if not all(k in data for k in ['report_id', 'claims', 'pages']):
            print(f"❌ Missing required fields in .claims.json")
            return False

        return True
    except Exception as e:
        print(f"❌ Error reading .claims.json: {e}")
        return False


def test_idempotency(report_id):
    """Test that re-extracting returns cached claims"""
    print("\n=== Test 5: Idempotency (Re-extraction) ===")

    payload = {'report_id': report_id}

    print(f"Sending second extraction request (should return cached claims immediately)...")

    response = requests.post(
        f"{API_BASE_URL}/extract_claims",
        json=payload,
        timeout=30  # Should be much faster since cached
    )

    if response.status_code != 200:
        print(f"❌ Re-extraction failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()
    print(f"✓ Re-extraction successful (returned cached claims)")
    print(f"  Message: {data.get('message')}")
    print(f"  Claims: {len(data.get('claims', []))}")

    return True


def test_extract_without_upload():
    """Test that extracting without upload fails properly"""
    print("\n=== Test 6: Extract Without Upload (Error Case) ===")

    payload = {'report_id': 'nonexistent-uuid-12345'}

    response = requests.post(
        f"{API_BASE_URL}/extract_claims",
        json=payload,
        timeout=30
    )

    if response.status_code == 404:
        print(f"✓ Correctly returns 404 error")
        print(f"  Error message: {response.json().get('detail')}")
        return True
    else:
        print(f"❌ Expected 404, got {response.status_code}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Separated Upload and Extraction Flow")
    print("=" * 60)

    try:
        # Test 1: Upload without extraction
        report_id = test_upload_without_extraction()
        if not report_id:
            print("\n❌ Upload test failed, stopping here")
            return

        # Test 2: Verify .extracted.json
        if not test_extracted_json_exists(report_id):
            print("\n❌ .extracted.json verification failed")
            return

        # Test 3: Manual claim extraction
        claims = test_extract_claims(report_id)
        if not claims:
            print("\n❌ Extraction test failed")
            return

        # Test 4: Verify .claims.json
        if not test_claims_json_exists(report_id):
            print("\n❌ .claims.json verification failed")
            return

        # Test 5: Idempotency
        if not test_idempotency(report_id):
            print("\n❌ Idempotency test failed")
            return

        # Test 6: Error handling
        if not test_extract_without_upload():
            print("\n❌ Error handling test failed")
            return

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Failed to connect to API. Make sure the backend is running:")
        print("   cd rag_demo/backend")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
